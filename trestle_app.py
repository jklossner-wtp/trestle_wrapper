from fastapi import FastAPI, HTTPException, Request
import httpx, os, time, logging
from pydantic import BaseModel

class MLSListingsRequest(BaseModel):
    credentials: dict
    filters: dict
    mls_vendor:  str
    mls_client:  str

CLIENT_ID  = os.getenv("TRESTLE_ID")
CLIENT_SEC = os.getenv("TRESTLE_SEC")
TOKEN_URL  = "https://api-trestle.corelogic.com/trestle/oidc/connect/token"
BASE_URL   = "https://api-trestle.corelogic.com/trestle/odata"

app  = FastAPI(title="Trestle OData Proxy")
#log  = logging.getLogger("uvicorn.error")

logging.basicConfig(level=logging.DEBUG)
log  = logging.getLogger("uvicorn.access")
#log = logging.getLogger(__name__)

_tok = {"value": None, "exp": 0}      # 8-hour token cache :contentReference[oaicite:5]{index=5}

@app.get("/")
def root():
    print(f"testing this output")
    return {"status":"ok"}

@app.post("/mls-listings")
def mls_listings( request: MLSListingsRequest):
    return{"message": "test success"}

async def token() -> str:
    if _tok["exp"] < time.time():
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SEC,
            "grant_type": "client_credentials",
            "scope": "api",
        }
        print(f"Requesting token with: client_id={CLIENT_ID}, client_secret={'<set>' if CLIENT_SEC else '<missing>'}")
        async with httpx.AsyncClient() as c:
            r = await c.post(TOKEN_URL, data=data)
            r.raise_for_status()
            body = r.json()
        _tok.update(value=body["access_token"],
                    exp=time.time() + body["expires_in"] - 60)
    return _tok["value"]

async def query(path: str):
    headers = {"Authorization": f"Bearer {await token()}"}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.get(f"{BASE_URL}/{path}", headers=headers)
        if r.status_code == 429:
            raise HTTPException(429, "Trestle per-minute quota hit; retry shortly")
        r.raise_for_status()
        return r.json()

@app.get("/odata/{path:path}")
async def odata(path: str, request: Request):
    """Pass any RESO OData query straight through (URL-encode the $ signs)."""
#    path = "/odata/{path}"
#    log.debug(f"Sending request path: {path}")
#    print(f"Sending request path: {path}")
    query_string = str(request.url.query)
    if query_string:
        path = f"{path}?{query_string}"
    log.debug(f"Forwarding to Trestle path: {path}")
    print(f"Forwarding to Trestle path: {path}")
    return await query(path)

@app.get("/saved/{sid}")
async def saved(sid: int):
    """Return ListingKeys from a Saved Search, then fetch full details."""
    ids = await query(f"SavedSearches({sid})/Default.GetSavedSearchListingIDs()")
    keys = ",".join([f"'{k}'" for k in ids["value"]])
    return await query(f"Property?$filter=ListingKey in ({keys})")

