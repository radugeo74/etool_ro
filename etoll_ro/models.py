"""Interpret eToll data without Home Assistant or network dependencies."""

from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from .api import EtollError, parse_expiration

LOCAL_ZONE = ZoneInfo("Europe/Bucharest")
PAID_STATUSES = {"ACTIVE", "EXPIRED", "CONSUMED"}
EXCLUDED_STATUSES = {"DRAFT", "CANCELLED", "REFUNDED"}
SERVICE_TYPES = {"VIGNETTE", "BRIDGE", "ROUTE", "PER_KM"}


def next_bridge_expiration(passes, now):
    """Find the earliest known expiry of unused, still-valid crossings."""
    dates = []
    for entry in passes:
        if entry["remaining"] <= 0:
            continue
        expiry = entry["valid_until"]
        if expiry is None:
            return None  # This package might expire before any of the known ones.
        if expiry >= now:
            dates.append(expiry)
    return min(dates, default=None)


def last_complete_update(previous, snapshot):
    """A partial refresh must not claim that all displayed data is fresh."""
    required = ("services", "invoices", "notifications", "service_status")
    if all(snapshot["sections"].get(key) is True for key in required):
        return snapshot["updated_at"]
    return previous


def money(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise EtollError("Missing monetary value")
    try:
        result = Decimal(str(value))
    except InvalidOperation as err:
        raise EtollError("Invalid monetary value") from err
    if not result.is_finite():
        raise EtollError("Invalid monetary value")
    return result


def amount(value):
    return float(value.quantize(Decimal("0.01")))


def required_date(value):
    result = parse_expiration(value)
    if result is None:
        raise EtollError("Missing transaction date")
    return result


def invoice_summary(rows, now):
    """Sum paid invoices by Romanian calendar year, including per-km top-ups."""
    year = now.astimezone(LOCAL_ZONE).year
    totals = {str(y): Decimal(0) for y in range(year - 4, year + 1)}
    current_count = 0
    vat = Decimal(0)
    net = Decimal(0)
    latest = None
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"] or row["id"] in seen:
            raise EtollError("Invalid or duplicate invoice")
        seen.add(row["id"])
        paid = required_date(row.get("paymentDate"))
        price = row.get("total")
        if not isinstance(price, dict):
            raise EtollError("Invalid invoice total")
        gross = money(price.get("totalPrice"))
        invoice_year = str(paid.astimezone(LOCAL_ZONE).year)
        if paid > now:
            raise EtollError("Invoice payment date is in the future")
        if invoice_year not in totals:
            continue
        totals[invoice_year] += gross
        if invoice_year == str(year):
            current_count += 1
            vat += money(price.get("vat"))
            net += money(price.get("priceWithoutVat"))
        if latest is None or paid > latest["payment_date"]:
            latest = {
                "amount": amount(gross),
                "payment_date": paid,
                "invoice_number": " ".join(
                    str(v) for v in (row.get("externalSeries"), row.get("externalNumber")) if v is not None
                ),
                "payment_method": row.get("paymentMethod"),
                "services": row.get("types"),
                "amount_without_vat": amount(money(price.get("priceWithoutVat"))),
                "vat_amount": amount(money(price.get("vat"))),
                "vat_percentage": price.get("vatPercentage"),
            }
    return {
        "year": year,
        "total": amount(totals[str(year)]),
        "yearly_totals": {k: amount(v) for k, v in totals.items()},
        "invoice_count": current_count,
        "vat_amount": amount(vat),
        "amount_without_vat": amount(net),
        "latest": latest,
    }


def service_summary(rows, vehicles, now):
    """Do not conflate purchase costs with invoice payments or wallet balance."""
    year = now.astimezone(LOCAL_ZONE).year
    output = {}
    for vehicle_id, vehicle in vehicles.items():
        output[vehicle_id] = {
            "year": year,
            "total": Decimal(0),
            "yearly_totals": {str(y): Decimal(0) for y in range(year - 4, year + 1)},
            "vignette_amount": Decimal(0),
            "bridge_amount": Decimal(0),
            "route_amount": Decimal(0),
            "purchase_count": 0,
            "last_purchase": None,
            "bridge_remaining": 0,
            "bridge_passes": [],
            "current_vignette": None,
        }
    for row in rows:
        if not isinstance(row, dict):
            raise EtollError("Invalid service")
        state = row.get("status")
        if not isinstance(state, str):
            raise EtollError("Invalid service status")
        if state in EXCLUDED_STATUSES:
            continue
        if state not in PAID_STATUSES:
            raise EtollError("Unrecognized service status")
        kind = row.get("type")
        if not isinstance(kind, str):
            raise EtollError("Invalid service type")
        if kind not in SERVICE_TYPES:
            raise EtollError("Unrecognized service type")
        if kind == "PER_KM":
            continue  # Top-ups are account payments, not per-vehicle purchases.
        linked = row.get("vehicle")
        if not isinstance(linked, dict) or not linked.get("id"):
            raise EtollError("Missing service vehicle")
        vehicle_id = str(linked["id"])
        if vehicle_id not in output:
            continue
        summary = output[vehicle_id]
        purchased = required_date(row.get("firstTransactionDate"))
        price = row.get("price")
        if not isinstance(price, dict):
            raise EtollError("Missing service price")
        gross = money(price.get("totalPrice"))
        purchase_year = str(purchased.astimezone(LOCAL_ZONE).year)
        if purchased > now:
            raise EtollError("Service purchase date is in the future")
        if purchase_year in summary["yearly_totals"]:
            summary["yearly_totals"][purchase_year] += gross
        if purchase_year == str(year):
            summary["total"] += gross
            summary[{"VIGNETTE": "vignette_amount", "BRIDGE": "bridge_amount", "ROUTE": "route_amount"}[kind]] += gross
            summary["purchase_count"] += 1
        if summary["last_purchase"] is None or purchased > summary["last_purchase"]:
            summary["last_purchase"] = purchased
        valid_from = parse_expiration(row.get("validFrom"))
        valid_until = parse_expiration(row.get("validUntil"))
        if kind == "VIGNETTE" and valid_until is not None and valid_until == vehicles[vehicle_id].get("expires_at"):
            issuance = row.get("issuance") or {}
            summary["current_vignette"] = {
                "valid_from": valid_from,
                "valid_until": valid_until,
                "duration": row.get("duration"),
                "status": state,
                "price_paid": amount(gross),
                "purchased_at": purchased,
                "serial": issuance.get("serialNo") if isinstance(issuance, dict) else None,
            }
        if (
            kind == "BRIDGE"
            and state == "ACTIVE"
            and (valid_from is None or valid_from <= now)
            and (valid_until is None or now <= valid_until)
        ):
            balance = row.get("peajBalance")
            remaining = balance.get("remainingCrossingsCount") if isinstance(balance, dict) else None
            if type(remaining) is not int or remaining < 0:
                raise EtollError("Invalid bridge crossing balance")
            summary["bridge_remaining"] += remaining
            summary["bridge_passes"].append(
                {
                    "bridge": row.get("bridgeType"),
                    "remaining": remaining,
                    "initial": balance.get("initialCrossingsCount"),
                    "valid_until": valid_until,
                }
            )
    for summary in output.values():
        for key in ("total", "vignette_amount", "bridge_amount", "route_amount"):
            summary[key] = amount(summary[key])
        summary["yearly_totals"] = {k: amount(v) for k, v in summary["yearly_totals"].items()}
    return output


def notification_count(payload):
    count = payload.get("count") if isinstance(payload, dict) else None
    if type(count) is not int or count < 0:
        raise EtollError("Invalid notification summary")
    return count


def service_status(payload):
    try:
        attributes = payload["data"]["attributes"]
        code = attributes["status"]["value"]
        label = {1: "operational", 2: "performance_issues", 3: "partial_outage", 4: "major_outage"}[code]
        return {
            "state": label,
            "component": attributes["name"],
            "updated_at": attributes.get("updated", {}).get("string"),
        }
    except (KeyError, TypeError) as err:
        raise EtollError("Unrecognized service status") from err
