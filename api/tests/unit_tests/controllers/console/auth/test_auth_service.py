from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from constants import HEADER_NAME_ACCESS_TOKEN, HEADER_NAME_CSRF_TOKEN, HEADER_NAME_REFRESH_TOKEN
from controllers.console.auth.auth_service import AuthServiceLoginApi, _load_target_workspace
from controllers.console.auth.error import AuthServiceConfigurationError


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


class TestLoadTargetWorkspace:
    @patch("controllers.console.auth.auth_service.db")
    def test_load_target_workspace_returns_existing_workspace_by_name(self, mock_db):
        tenant = MagicMock()
        mock_db.session.scalar.return_value = tenant

        with (
            patch("controllers.console.auth.auth_service.dify_config.AUTH_SERVICE_DEFAULT_WORKSPACE_ID", None),
            patch("controllers.console.auth.auth_service.dify_config.AUTH_SERVICE_DEFAULT_WORKSPACE_NAME", "研发部门"),
            patch("controllers.console.auth.auth_service.dify_config.AUTH_SERVICE_DEFAULT_WORKSPACE_ROLE", "normal"),
        ):
            result = _load_target_workspace()

        assert result is tenant
        mock_db.session.scalar.assert_called_once()

    @patch("controllers.console.auth.auth_service.TenantService.create_tenant")
    @patch("controllers.console.auth.auth_service.db")
    def test_load_target_workspace_creates_workspace_when_name_not_found(self, mock_db, mock_create_tenant):
        tenant = MagicMock()
        mock_db.session.scalar.return_value = None
        mock_create_tenant.return_value = tenant

        with (
            patch("controllers.console.auth.auth_service.dify_config.AUTH_SERVICE_DEFAULT_WORKSPACE_ID", None),
            patch("controllers.console.auth.auth_service.dify_config.AUTH_SERVICE_DEFAULT_WORKSPACE_NAME", "研发部门"),
            patch("controllers.console.auth.auth_service.dify_config.AUTH_SERVICE_DEFAULT_WORKSPACE_ROLE", "normal"),
        ):
            result = _load_target_workspace()

        assert result is tenant
        mock_create_tenant.assert_called_once_with("研发部门", is_setup=True)

    def test_load_target_workspace_raises_when_id_and_name_are_both_missing(self):
        with (
            patch("controllers.console.auth.auth_service.dify_config.AUTH_SERVICE_DEFAULT_WORKSPACE_ID", None),
            patch("controllers.console.auth.auth_service.dify_config.AUTH_SERVICE_DEFAULT_WORKSPACE_NAME", None),
            patch("controllers.console.auth.auth_service.dify_config.AUTH_SERVICE_DEFAULT_WORKSPACE_ROLE", "normal"),
        ):
            with pytest.raises(AuthServiceConfigurationError, match="workspace id or name"):
                _load_target_workspace()
