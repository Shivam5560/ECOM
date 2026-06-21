from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any

from core_common.auth import TokenClaims

try:
    import bcrypt
except ModuleNotFoundError:
    bcrypt = None


class PasswordHasher:
    def hash_password(self, password: str) -> str:
        if bcrypt is None:
            raise RuntimeError("bcrypt is required for password hashing")
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")

    def verify_password(self, password: str, hashed_password: str) -> bool:
        if bcrypt is None:
            raise RuntimeError("bcrypt is required for password verification")
        if not hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
            return False
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("ascii"))


@dataclass(frozen=True, slots=True)
class TokenIssuer:
    issuer: str
    key_id: str
    private_key: str
    public_key: str

    def issue_access_token(
        self,
        *,
        subject: str,
        email: str,
        roles: list[str],
        expires_in_seconds: int = 900,
    ) -> str:
        now = int(time.time())
        header = {"alg": "RS256", "typ": "JWT", "kid": self.key_id}
        payload = {
            "iss": self.issuer,
            "sub": subject,
            "email": email,
            "roles": roles,
            "iat": now,
            "exp": now + expires_in_seconds,
        }
        signing_input = ".".join([self._encode_json(header), self._encode_json(payload)])
        signature = self._sign(signing_input)
        return f"{signing_input}.{signature}"

    def verify_token(self, token: str, *, now: int | None = None) -> TokenClaims:
        try:
            encoded_header, encoded_payload, signature = token.split(".", 2)
        except ValueError as exc:
            raise ValueError("invalid token format") from exc
        signing_input = f"{encoded_header}.{encoded_payload}"
        expected = self._sign(signing_input)
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid token signature")
        payload = self._decode_json(encoded_payload)
        current_time = int(time.time()) if now is None else now
        if int(payload["exp"]) < current_time:
            raise ValueError("token expired")
        return TokenClaims(
            sub=str(payload["sub"]),
            email=payload.get("email"),
            roles=list(payload.get("roles", [])),
            exp=int(payload["exp"]),
        )

    def jwks(self) -> dict[str, list[dict[str, str]]]:
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "kid": self.key_id,
                    "alg": "RS256",
                    "k": self.public_key,
                }
            ]
        }

    def _sign(self, signing_input: str) -> str:
        digest = hmac.new(
            self.private_key.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return self._encode_bytes(digest)

    def _encode_json(self, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return self._encode_bytes(raw)

    def _decode_json(self, payload: str) -> dict[str, Any]:
        return json.loads(self._decode_bytes(payload).decode("utf-8"))

    def _encode_bytes(self, payload: bytes) -> str:
        return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")

    def _decode_bytes(self, payload: str) -> bytes:
        padded = payload + "=" * (-len(payload) % 4)
        return base64.urlsafe_b64decode(padded.encode("ascii"))
