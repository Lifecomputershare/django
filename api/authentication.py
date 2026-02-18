import base64
import hashlib
import hmac
import json
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication


User = get_user_model()


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _encode_jwt(payload: dict, exp_seconds: int) -> str:
    secret = settings.SECRET_KEY
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    data = payload.copy()
    data["iat"] = now
    data["exp"] = now + exp_seconds
    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _base64url_encode(json.dumps(data, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = _base64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def _decode_jwt(token: str) -> dict:
    secret = settings.SECRET_KEY
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError:
        raise exceptions.AuthenticationFailed("Invalid token format")
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    try:
        signature = _base64url_decode(signature_b64)
    except Exception:
        raise exceptions.AuthenticationFailed("Invalid token signature")
    if not hmac.compare_digest(expected_signature, signature):
        raise exceptions.AuthenticationFailed("Invalid token signature")
    try:
        payload_bytes = _base64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        raise exceptions.AuthenticationFailed("Invalid token payload")
    exp = payload.get("exp")
    if exp is not None and int(time.time()) > int(exp):
        raise exceptions.AuthenticationFailed("Token has expired")
    return payload


def generate_access_token(user: User) -> str:
    return _encode_jwt({"user_id": user.id, "type": "access"}, exp_seconds=60 * 15)


def generate_refresh_token(user: User) -> str:
    return _encode_jwt({"user_id": user.id, "type": "refresh"}, exp_seconds=60 * 60 * 24 * 7)


def decode_token(token: str, expected_type: str) -> dict:
    payload = _decode_jwt(token)
    token_type = payload.get("type")
    if token_type != expected_type:
        raise exceptions.AuthenticationFailed("Invalid token type")
    return payload


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = request.headers.get("Authorization") or ""
        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        token = parts[1]
        payload = decode_token(token, "access")
        user_id = payload.get("user_id")
        if not user_id:
            raise exceptions.AuthenticationFailed("Invalid token payload")
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found")
        return user, None

