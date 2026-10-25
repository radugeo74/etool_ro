"""Constants for the independent eToll reader."""

DOMAIN = "etoll_ro"
NAME = "eToll România"
TOKEN_URL = "https://sso.etoll.ro/auth/realms/external/protocol/openid-connect/token"
API_URL = "https://portal.etoll.ro/api/"
CLIENT_ID = "ddcm-authz-client"
UPDATE_MINUTES = 30

# Portal labels and current bounds from /api/resources/mtmaLimits (2026-10-25).
VEHICLE_CATEGORY_LABELS = {
    "A": "A — Autoturisme (sub 8+1 locuri)",
    "B": "B — Transport marfă (MTMA ≤ 3,5 t)",
    "C": "C — Transport persoane (între 9 și 23 de locuri pe scaune)",
    "D": "D — Transport persoane (mai mult de 23 de locuri pe scaune)",
    "I": "I — Transport marfă (3,5 t < MTMA ≤ 7,5 t)",
    "II": "II — Transport marfă (7,5 t < MTMA < 12 t)",
    "III": "III — Transport marfă (MTMA ≥ 12 t)",
}
