"""Unit tests for security module (JWT tokens, password hashing)."""

from backend.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """Password hashing and verification tests."""

    def test_hash_and_verify_correct(self):
        hashed = hash_password("mypassword123")
        assert verify_password("mypassword123", hashed) is True

    def test_hash_and_verify_wrong_password(self):
        hashed = hash_password("mypassword123")
        assert verify_password("wrongpassword", hashed) is False

    def test_hash_is_different_from_plain(self):
        hashed = hash_password("test")
        assert hashed != "test"

    def test_hash_is_unique_per_call(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # Different salts


class TestJWTTokens:
    """JWT token creation and decoding tests."""

    def test_access_token_has_type(self):
        token = create_access_token({"sub": "user123"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "access"

    def test_refresh_token_has_type(self):
        token = create_refresh_token({"sub": "user123"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"

    def test_tokens_have_jti(self):
        access = create_access_token({"sub": "user123"})
        refresh = create_refresh_token({"sub": "user123"})

        access_payload = decode_token(access)
        refresh_payload = decode_token(refresh)

        assert access_payload is not None
        assert "jti" in access_payload
        assert refresh_payload is not None
        assert "jti" in refresh_payload
        # JTIs should be unique
        assert access_payload["jti"] != refresh_payload["jti"]

    def test_token_contains_data(self):
        token = create_access_token({"sub": "user-abc", "tenant_id": "tenant-xyz"})
        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "user-abc"
        assert payload["tenant_id"] == "tenant-xyz"

    def test_decode_invalid_token_returns_none(self):
        assert decode_token("invalid.token.here") is None
        assert decode_token("") is None
        assert decode_token("not-a-jwt") is None

    def test_token_has_expiration(self):
        token = create_access_token({"sub": "user123"})
        payload = decode_token(token)

        assert payload is not None
        assert "exp" in payload

    def test_each_token_has_unique_jti(self):
        t1 = create_access_token({"sub": "user123"})
        t2 = create_access_token({"sub": "user123"})

        p1 = decode_token(t1)
        p2 = decode_token(t2)

        assert p1 is not None and p2 is not None
        assert p1["jti"] != p2["jti"]
