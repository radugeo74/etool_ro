"""Small read-only eToll client. No license service or telemetry."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import aiohttp

from .const import API_URL, CLIENT_ID, TOKEN_URL


class EtollError(Exception):
    """Sanitized service/protocol failure."""


class AuthenticationError(EtollError):
    """Credentials require user attention."""


class UnsupportedAuthentication(EtollError):
    """The SSO client does not permit this authentication flow."""


class ProfileChanged(EtollError):
    """Current profile changed; do not associate its data with the old profile."""


def parse_expiration(value: Any) -> datetime | None:
    """Return an aware timestamp; never invent midnight for a date-only value."""
    if value is None:
        return None
    if not isinstance(value, str) or "T" not in value:
        raise EtollError("Invalid expiration timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            result = result.replace(tzinfo=ZoneInfo("Europe/Bucharest"))
        return result.astimezone(timezone.utc)
    except (ValueError, OverflowError) as err:
        raise EtollError("Invalid expiration timestamp") from err


def normalize_vehicle(raw: Any) -> dict[str, Any]:
    """Allowlist fields for local entities; diagnostics never include these values."""
    if not isinstance(raw, dict) or not raw.get("id") or not raw.get("plateNumber"):
        raise EtollError("Invalid vehicle response")
    eligibility = raw.get("vignetteEligibility")
    if eligibility is not None and not isinstance(eligibility, dict):
        raise EtollError("Invalid vignette eligibility response")
    # Missing eligibility is unknown, not an expired/missing vignette.
    known = (
        isinstance(raw.get("category"), str)
        and raw.get("category") in {"A", "B", "C", "D"}
        and isinstance(eligibility, dict)
        and "expirationDateCurrentVignette" in eligibility
    )
    expiry = parse_expiration(eligibility["expirationDateCurrentVignette"]) if known else None
    return {
        "id": str(raw["id"]),
        "plate": str(raw["plateNumber"]),
        "category": raw.get("category"),
        "vehicle_type": raw.get("vehicleType"),
        "eligibility_known": known,
        "expires_at": expiry,
        "details": {
            key: raw[key]
            for key in (
                "plateNumber",
                "vin",
                "registrationSerial",
                "emissionStandard",
                "countryCode",
                "mtma",
                "strrPeajCategoryCode",
                "temporaryPlate",
                "favorite",
                "vehicleType",
            )
            if raw.get(key) is not None and isinstance(raw[key], (str, int, float, bool))
        },
        "data_valid": raw.get("isValid") if type(raw.get("isValid")) is bool else None,
    }


class EtollClient:
    """Use the official SSO and GET requests for account data only."""

    def __init__(self, session: aiohttp.ClientSession, username: str, password: str):
        self._session = session
        self._username = username
        self._password = password
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at = 0.0
        self._lock = asyncio.Lock()

    async def _json(self, method: str, url: str, **kwargs: Any) -> tuple[int, Any]:
        try:
            async with self._session.request(
                method,
                url,
                timeout=aiohttp.ClientTimeout(total=30),
                allow_redirects=False,
                **kwargs,
            ) as response:
                # Never include URLs, bodies, passwords or tokens in exceptions/logs.
                if response.status == 429:
                    raise EtollError("Service rate limit reached; wait for the next update")
                if response.status >= 500:
                    raise EtollError("eToll temporarily unavailable")
                if 300 <= response.status < 400:
                    raise EtollError("Unexpected service redirect")
                try:
                    body = await response.json()
                except (ValueError, aiohttp.ContentTypeError) as err:
                    raise EtollError("Service returned an invalid JSON response") from err
                return response.status, body
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise EtollError("Could not connect to eToll") from err

    async def _token(self, *, force: bool = False) -> None:
        async with self._lock:
            if not force and self._access_token and time.monotonic() < self._expires_at:
                return
            form = {"client_id": CLIENT_ID}
            if self._refresh_token:
                form.update(grant_type="refresh_token", refresh_token=self._refresh_token)
            else:
                form.update(
                    grant_type="password", username=self._username, password=self._password, scope="openid profile"
                )
            status, payload = await self._json("POST", TOKEN_URL, data=form)
            error = payload.get("error") if isinstance(payload, dict) else None
            if status == 400 and error == "invalid_grant" and self._refresh_token:
                self._refresh_token = None
                form = {
                    "client_id": CLIENT_ID,
                    "grant_type": "password",
                    "username": self._username,
                    "password": self._password,
                    "scope": "openid profile",
                }
                status, payload = await self._json("POST", TOKEN_URL, data=form)
                error = payload.get("error") if isinstance(payload, dict) else None
            if error in {"unauthorized_client", "invalid_client", "unsupported_grant_type"}:
                raise UnsupportedAuthentication("SSO does not allow direct authentication for this client")
            if status in (400, 401, 403) and error in {"invalid_grant", "access_denied"}:
                raise AuthenticationError("Authentication rejected")
            if status != 200 or not isinstance(payload, dict):
                raise EtollError("Unexpected SSO response")
            access = payload.get("access_token")
            refresh = payload.get("refresh_token")
            lifetime = payload.get("expires_in")
            if not isinstance(access, str) or not access or not isinstance(lifetime, (int, float)) or lifetime <= 0:
                raise EtollError("Invalid SSO token response")
            if refresh is not None and not isinstance(refresh, str):
                raise EtollError("Invalid SSO refresh token response")
            self._access_token = access
            self._refresh_token = refresh
            self._expires_at = time.monotonic() + max(0, lifetime - 60)

    async def _get(self, path: str, params: dict | None = None) -> Any:
        await self._token()
        for attempt in range(2):
            status, payload = await self._json(
                "GET",
                API_URL + path,
                params=params,
                headers={"Authorization": f"Bearer {self._access_token}", "Accept": "application/json"},
            )
            if status == 401:
                if attempt == 0:
                    await self._token(force=True)
                    continue
                raise AuthenticationError("Account session rejected")
            if status == 403:
                raise EtollError("Account does not have access to this resource")
            if status != 200:
                raise EtollError(f"Unexpected API status ({status})")
            return payload
        raise AuthenticationError("Account session rejected")

    async def profile(self) -> dict[str, str]:
        payload = await self._get("profiles")
        # The public portal's ProfileListResult has a Profiles collection.
        profiles = (
            payload if isinstance(payload, list) else payload.get("profiles") if isinstance(payload, dict) else None
        )
        if not isinstance(profiles, list) or any(not isinstance(p, dict) for p in profiles):
            raise EtollError("Unrecognized profiles response")
        current = [p for p in profiles if p.get("isCurrent") is True]
        if len(current) != 1 or not current[0].get("id"):
            raise EtollError("Select a current profile in the eToll portal first")
        return {"id": str(current[0]["id"]), "name": str(current[0].get("name") or "eToll")}

    async def snapshot(self, profile_id: str) -> dict[str, dict]:
        if (await self.profile())["id"] != profile_id:
            raise ProfileChanged("Current eToll profile changed; restore it in the portal")
        vehicles: dict[str, dict] = {}
        cursor: str | None = None
        seen: set[str] = set()
        for _ in range(100):
            params = {"vehicleType": "CAR", "computeVignetteEligibility": "true", "size": "50"}
            if cursor:
                params["cursor"] = cursor
            payload = await self._get("vehicles", params)
            if not isinstance(payload, dict) or not isinstance(payload.get("vehicles"), list):
                raise EtollError("Unrecognized vehicles page")
            for raw in payload["vehicles"]:
                vehicle = normalize_vehicle(raw)
                if vehicle["id"] in vehicles:
                    raise EtollError("Duplicate vehicle across pages; retry next update")
                vehicles[vehicle["id"]] = vehicle
            cursor = payload.get("nextCursor")
            if cursor is None or cursor == "":
                break
            if not isinstance(cursor, str) or cursor in seen:
                raise EtollError("Invalid pagination cursor")
            seen.add(cursor)
        else:
            raise EtollError("Pagination limit exceeded")
        # A profile may be switched in the mobile app during pagination.
        if (await self.profile())["id"] != profile_id:
            raise ProfileChanged("Current eToll profile changed during update")
        return vehicles

    async def _tolls(self):
        # Explicit statuses avoid relying on the portal's default filter.
        rows, seen = [], set()
        for state in ("ACTIVE", "EXPIRED", "CONSUMED"):
            for row in await self._toll_pages(state):
                if row["id"] in seen:
                    raise EtollError("Service changed status during pagination; retry next update")
                seen.add(row["id"])
                rows.append(row)
        return rows

    async def _toll_pages(self, state):
        rows, seen_ids, seen_cursors = [], set(), set()
        params = {"size": "100", "status": state}
        for _ in range(100):
            payload = await self._get("tolls", params.copy())
            if not isinstance(payload, dict) or not isinstance(payload.get("tolls"), list) or payload.get("errors"):
                raise EtollError("Unrecognized or incomplete services response")
            for row in payload["tolls"]:
                if not isinstance(row, dict) or not isinstance(row.get("id"), str) or row["id"] in seen_ids:
                    raise EtollError("Invalid or duplicate service")
                if row.get("status") != state:
                    raise EtollError("Service status filter was not respected")
                seen_ids.add(row["id"])
                rows.append(row)
            cursor = payload.get("nextCursor")
            if cursor is None or cursor == "":
                return rows
            if not isinstance(cursor, str) or cursor in seen_cursors:
                raise EtollError("Invalid services pagination")
            seen_cursors.add(cursor)
            params["cursor"] = cursor
        raise EtollError("Services pagination limit exceeded")

    async def dashboard(self, profile_id: str):
        """Publish optional sections independently, while enforcing profile identity."""
        from .models import LOCAL_ZONE, invoice_summary, notification_count, service_status, service_summary

        now = datetime.now(timezone.utc)
        vehicles = await self.snapshot(profile_id)
        account, sections = {}, {}

        async def section(name, fetch, normalize):
            try:
                value = normalize(await fetch())
            except AuthenticationError:
                raise
            except EtollError:
                sections[name] = False
                return None
            sections[name] = True
            return value

        start = datetime(now.astimezone(LOCAL_ZONE).year - 4, 1, 1, tzinfo=LOCAL_ZONE)

        async def invoices():
            rows = await self._get(
                "invoices",
                {"from": start.isoformat(timespec="milliseconds"), "to": now.isoformat(timespec="milliseconds")},
            )
            if not isinstance(rows, list):
                raise EtollError("Unrecognized invoices response")
            return rows

        async def status():
            code, payload = await self._json("GET", "https://portal.etoll.ro/status/api/components/1")
            if code != 200:
                raise EtollError("Status endpoint unavailable")
            return payload

        services = await section("services", self._tolls, lambda rows: service_summary(rows, vehicles, now))
        if services is not None:
            for vehicle_id, summary in services.items():
                vehicles[vehicle_id]["services"] = summary
        account["invoices"] = await section("invoices", invoices, lambda rows: invoice_summary(rows, now))
        account["notifications"] = await section(
            "notifications", lambda: self._get("notifications/summary"), notification_count
        )
        account["service_status"] = await section("service_status", status, service_status)
        if (await self.profile())["id"] != profile_id:
            raise ProfileChanged("Current eToll profile changed during update")
        return {
            "vehicles": vehicles,
            "account": account,
            "sections": sections,
            "updated_at": datetime.now(timezone.utc),
        }
