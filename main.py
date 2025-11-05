import time
import string
import hashlib
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from webauthn import verify_registration_response, verify_authentication_response
from webauthn.helpers import base64url_to_bytes
from db import add_user, update_user, get_user_by_id

app = FastAPI()

RP_ID = "localhost"
RP_NAME = "My App"
ORIGIN = "http://localhost:8001"

app.mount("/static", StaticFiles(directory="static"), name="static")


class RegisterRequest(BaseModel):
    credential: Dict[str, Any]
    userIdHex: str


class LoginRequest(BaseModel):
    credential: Dict[str, Any]
    apiKeyPublicHex: str
    timestamp: int


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")


@app.post("/register")
async def register_complete(data: RegisterRequest):
    verification = verify_registration_response(
        credential=data.credential,
        expected_challenge=bytes.fromhex(data.userIdHex),
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
    )

    if not verification.user_verified:
        raise HTTPException(status_code=400, detail="Verification failed")

    record = {
        "user_id": data.userIdHex,
        "credential_id": verification.credential_id.hex(),
        "public_key": verification.credential_public_key.hex(),
        "sign_count": verification.sign_count,
        "timestamp": 0,
    }
    add_user(data.userIdHex, record)
    return {"success": True, "user": record}


@app.post("/login")
async def login_complete(data: LoginRequest):
    api_key_public_hex = data.apiKeyPublicHex
    timestamp = int(data.timestamp)

    def is_hex(s: str) -> bool:
        return all(c in string.hexdigits for c in s)

    if not (is_hex(api_key_public_hex) and len(api_key_public_hex) == 64):
        raise HTTPException(status_code=400, detail="Invalid apiKeyPublicHex")

    now = int(time.time())
    if not (now - 60 < timestamp < now + 60):
        raise HTTPException(status_code=400, detail="Timestamp out of range")

    msg = bytes.fromhex(api_key_public_hex) + timestamp.to_bytes(8, "big")
    expected_challenge = hashlib.sha256(msg).digest()

    user_id_b64 = data.credential["response"]["userHandle"]
    user_id = base64url_to_bytes(user_id_b64)
    user_id_hex = user_id.hex()

    user = get_user_by_id(user_id_hex)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["timestamp"] >= timestamp:
        raise HTTPException(status_code=400, detail="Replay detected")

    verification = verify_authentication_response(
        credential=data.credential,
        expected_challenge=expected_challenge,
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
        credential_public_key=bytes.fromhex(user["public_key"]),
        credential_current_sign_count=user["sign_count"],
    )

    if not verification.user_verified:
        raise HTTPException(status_code=400, detail="Verification failed")

    update_user(
        user_id_hex,
        {
            "sign_count": verification.new_sign_count,
            "api_key_public_hex": api_key_public_hex,
            "timestamp": timestamp,
        },
    )

    return {
        "success": True,
        "user_id": user_id_hex,
        "new_sign_count": verification.new_sign_count,
        "timestamp": timestamp,
    }
