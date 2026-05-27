from unittest.mock import MagicMock, patch

from flask import Flask

from constants import HEADER_NAME_ACCESS_TOKEN, HEADER_NAME_CSRF_TOKEN, HEADER_NAME_REFRESH_TOKEN
from controllers.console.auth.auth_service import AuthServiceLoginApi


class TestAuthServiceLoginApi:
    @patch("controllers.console.wraps.db")
    @patch("controllers.console.auth.auth_service._ensure_workspace_membership")
    @patch("controllers.console.auth.auth_service._get_or_create_account")
    @patch("controllers.console.auth.auth_service._load_target_workspace")
    @patch("controllers.console.auth.auth_service.AuthServiceClient")
    @patch("controllers.console.auth.auth_service.AccountService.login")
    def test_auth_service_login_returns_tokens_in_headers_and_body(
        self,
        mock_login,
        mock_client_cls,
        mock_load_workspace,
        mock_get_or_create_account,
        mock_ensure_workspace_membership,
        mock_db,
    ):
        app = Flask(__name__)
        app.config["TESTING"] = True

        mock_client = MagicMock()
        mock_client.check_token.return_value = {"sub": "external-user-1"}
        mock_client.get_user_info.return_value = MagicMock(
            user_id="fallback-user-id",
            user_name="Test User",
            email="user@example.com",
        )
        mock_client_cls.return_value = mock_client

        mock_workspace = MagicMock()
        mock_account = MagicMock()
        mock_token_pair = MagicMock(
            access_token="access-token",
            refresh_token="refresh-token",
            csrf_token="csrf-token",
        )

        mock_load_workspace.return_value = mock_workspace
        mock_get_or_create_account.return_value = mock_account
        mock_login.return_value = mock_token_pair

        with app.test_request_context(
            "/auth-service/login",
            method="POST",
            json={"token": "auth-service-token"},
        ):
            response = AuthServiceLoginApi().post()

        mock_client.check_token.assert_called_once_with("auth-service-token")
        mock_client.get_user_info.assert_called_once_with("auth-service-token")
        mock_ensure_workspace_membership.assert_called_once_with(mock_account, mock_workspace)
        assert response.json["result"] == "success"
        assert response.json["data"]["access_token"] == "access-token"
        assert response.json["data"]["refresh_token"] == "refresh-token"
        assert response.json["data"]["csrf_token"] == "csrf-token"
        assert response.headers[HEADER_NAME_ACCESS_TOKEN] == "Bearer access-token"
        assert response.headers[HEADER_NAME_REFRESH_TOKEN] == "refresh-token"
        assert response.headers[HEADER_NAME_CSRF_TOKEN] == "csrf-token"
