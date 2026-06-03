import jwt
import pytest
from fastapi import HTTPException
from fastapi_startkit.masoniteorm.testing import RefreshDatabase

from app.http.controllers.auth_controller import AuthController
from app.http.schemas.auth import LoginRequest, VerifyRequest
from app.models.identity import Identity
from app.services import hashing
from app.services.jwt_service import get_jwt_service
from tests.test_case import TestCase


class TestAuth(RefreshDatabase, TestCase):
    async def _seed(self):
        await Identity.first_or_create(
            {"tenant": "tenant-a", "email": "admin@tenant-a.com"},
            {
                "tenant": "tenant-a",
                "email": "admin@tenant-a.com",
                "name": "Admin",
                "password": hashing.make("secret"),
                "is_active": True,
            },
        )

    async def test_login_success_issues_jwt(self):
        await self._seed()

        resp = await AuthController.login(
            LoginRequest(tenant="tenant-a", email="admin@tenant-a.com", password="secret")
        )

        assert resp.token_type == "bearer"
        assert resp.expires_in == get_jwt_service().ttl

        claims = get_jwt_service().decode(resp.access_token)
        assert claims["tenant"] == "tenant-a"
        assert claims["email"] == "admin@tenant-a.com"
        assert "sub" in claims

    async def test_login_wrong_password_is_401(self):
        await self._seed()

        with pytest.raises(HTTPException) as exc:
            await AuthController.login(
                LoginRequest(tenant="tenant-a", email="admin@tenant-a.com", password="nope")
            )
        assert exc.value.status_code == 401

    async def test_login_unknown_tenant_is_401(self):
        await self._seed()

        with pytest.raises(HTTPException) as exc:
            await AuthController.login(
                LoginRequest(tenant="tenant-z", email="admin@tenant-a.com", password="secret")
            )
        assert exc.value.status_code == 401

    async def test_me_returns_identity_without_password(self):
        await self._seed()

        login = await AuthController.login(
            LoginRequest(tenant="tenant-a", email="admin@tenant-a.com", password="secret")
        )
        claims = get_jwt_service().decode(login.access_token)

        me = await AuthController.me(claims=claims)
        assert me["email"] == "admin@tenant-a.com"
        assert "password" not in me

    async def test_verify_accepts_issued_token(self):
        await self._seed()

        login = await AuthController.login(
            LoginRequest(tenant="tenant-a", email="admin@tenant-a.com", password="secret")
        )
        result = await AuthController.verify(VerifyRequest(token=login.access_token))
        assert result["valid"] is True
        assert result["claims"]["tenant"] == "tenant-a"

    async def test_verify_rejects_garbage_token(self):
        with pytest.raises(HTTPException) as exc:
            await AuthController.verify(VerifyRequest(token="not-a-real-token"))
        assert exc.value.status_code == 401

    async def test_tampered_token_fails_signature(self):
        await self._seed()

        login = await AuthController.login(
            LoginRequest(tenant="tenant-a", email="admin@tenant-a.com", password="secret")
        )
        with pytest.raises(jwt.PyJWTError):
            # Wrong secret must not verify.
            jwt.decode(
                login.access_token,
                "a-different-secret-also-at-least-32-bytes",
                algorithms=["HS256"],
            )
