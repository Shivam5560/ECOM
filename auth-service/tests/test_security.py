import time
import unittest

from auth_service.security import PasswordHasher, TokenIssuer


class AuthSecurityTests(unittest.TestCase):
    def test_password_hash_does_not_store_plaintext(self) -> None:
        hasher = PasswordHasher()

        hashed = hasher.hash_password("secret-password")

        self.assertNotEqual(hashed, "secret-password")
        self.assertTrue(hasher.verify_password("secret-password", hashed))
        self.assertFalse(hasher.verify_password("wrong-password", hashed))

    def test_token_issuer_round_trips_claims(self) -> None:
        issuer = TokenIssuer(
            issuer="auth-service",
            key_id="local-dev",
            private_key="test-private-key",
            public_key="test-public-key",
        )

        token = issuer.issue_access_token(
            subject="auth-1",
            email="user@example.com",
            roles=["customer"],
            expires_in_seconds=60,
        )
        claims = issuer.verify_token(token)

        self.assertEqual(claims.sub, "auth-1")
        self.assertEqual(claims.email, "user@example.com")
        self.assertEqual(claims.roles, ["customer"])

    def test_token_issuer_rejects_expired_token(self) -> None:
        issuer = TokenIssuer(
            issuer="auth-service",
            key_id="local-dev",
            private_key="test-private-key",
            public_key="test-public-key",
        )

        token = issuer.issue_access_token(
            subject="auth-1",
            email="user@example.com",
            roles=[],
            expires_in_seconds=-1,
        )

        with self.assertRaises(ValueError):
            issuer.verify_token(token, now=int(time.time()))

    def test_jwks_exposes_public_key_only(self) -> None:
        issuer = TokenIssuer(
            issuer="auth-service",
            key_id="local-dev",
            private_key="test-private-key",
            public_key="test-public-key",
        )

        jwks = issuer.jwks()

        self.assertEqual(jwks["keys"][0]["kid"], "local-dev")
        self.assertEqual(jwks["keys"][0]["use"], "sig")
        self.assertEqual(jwks["keys"][0]["k"], "test-public-key")
        self.assertNotIn("test-private-key", str(jwks))


if __name__ == "__main__":
    unittest.main()
