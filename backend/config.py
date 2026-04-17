import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRETS_PATH = BASE_DIR / "config" / "secrets.json"

with open(SECRETS_PATH) as f:
    _secrets = json.load(f)

DATABASE = _secrets["database"]
PAYMENT_GATEWAY = _secrets["payment_gateway"]
INTERNAL_API = _secrets["internal_api"]

DATABASE_URL = (
    f"postgresql://{DATABASE['username']}:{DATABASE['password']}"
    f"@{DATABASE['host']}:{DATABASE['port']}/meridian"
)

PAYMENT_API_KEY = PAYMENT_GATEWAY["api_key"]
WEBHOOK_SECRET = PAYMENT_GATEWAY["webhook_secret"]

INTERNAL_API_ENDPOINT = INTERNAL_API["endpoint"]
INTERNAL_API_TOKEN = INTERNAL_API["token"]
