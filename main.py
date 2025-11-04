from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from webauthn import (
    verify_registration_response,
    verify_authentication_response,
)
from webauthn.helpers import base64url_to_bytes
from db import add_user, get_user_by_id, set_user_sign_count

app = FastAPI()

# === Configuration ===
RP_ID = "localhost"  # your domain in production
RP_NAME = "My App"
ORIGIN = "http://localhost:8000"  # must match frontend origin
sessions = {}  # temporary challenge/session store

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")


@app.post("/register")
async def register_complete(request: Request):
    body = await request.json()
    credential = body.get("credential")
    user_id_hex = body.get("userIdHex")

    verification = verify_registration_response(
        credential=credential,
        expected_challenge=bytes.fromhex(user_id_hex),
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
    )

    if not verification.user_verified:
        return JSONResponse(status_code=400, content={"error": "Verification failed"})

    add_user(
        user_id_hex,
        verification.credential_id.hex(),
        verification.credential_public_key.hex(),
        verification.sign_count,
    )
    return {
        "success": True,
        "userIdHex": user_id_hex,
        "user": get_user_by_id(user_id_hex),
    }


@app.post("/login")
async def login_complete(request: Request):
    body = await request.json()
    credential = body.get("credential")
    api_key_public_hex = body.get("apiKeyPublicHex")

    user_id_b64 = credential["response"]["userHandle"]
    user_id = base64url_to_bytes(user_id_b64)
    user_id_hex = user_id.hex()

    user = get_user_by_id(user_id_hex)
    if not user:
        return JSONResponse(status_code=404, content={"error": "User not found"})

    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=bytes.fromhex(api_key_public_hex),
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
        credential_public_key=bytes.fromhex(user["public_key"]),
        credential_current_sign_count=user["sign_count"],
    )

    if not verification.user_verified:
        return JSONResponse(status_code=400, content={"error": "Verification failed"})

    print(user_id_hex, verification.new_sign_count, verification)
    set_user_sign_count(user_id_hex, verification.new_sign_count)
    return {
        "success": True,
        "userIdHex": user_id_hex,
        "user": user,
        "apiKeyPublicHex": api_key_public_hex,
    }
