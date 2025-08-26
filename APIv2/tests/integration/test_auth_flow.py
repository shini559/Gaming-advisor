from time import sleep

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

class TestAuthenticationFlow:
    @pytest.mark.asyncio
    async def test_complete_auth_flow(self, async_client: AsyncClient, db_session: AsyncSession, test_user_data):
        """Test flux complet : register → login → refresh → logout"""

        # 1. Register
        register_response = await async_client.post("/auth/register", json=test_user_data)
        assert register_response.status_code == 201

        # 2. Login
        login_response = await async_client.post("/auth/login", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        assert login_response.status_code == 200
        tokens = login_response.json()

        # 3. Verify access token works
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        me_response = await async_client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200

        # 4. Refresh tokens
        sleep(1)
        refresh_response = await async_client.post("/auth/refresh", json={
            "refresh_token": tokens["refresh_token"]
        })
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()

        # Verify tokens are different
        assert new_tokens["access_token"] != tokens["access_token"]
        assert new_tokens["refresh_token"] != tokens["refresh_token"]

        # 5. Old refresh token should be invalid
        old_refresh_response = await async_client.post("/auth/refresh", json={
            "refresh_token": tokens["refresh_token"]
        })
        assert old_refresh_response.status_code == 401

        # 6. Logout
        logout_response = await async_client.post("/auth/logout", json={
            "refresh_token": new_tokens["refresh_token"]
        }, headers={"Authorization": f"Bearer {new_tokens['access_token']}"})
        assert logout_response.status_code == 200