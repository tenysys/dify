import logging
import re

from flask import make_response, request
from flask_restx import Resource
from pydantic import BaseModel, Field
from sqlalchemy import select
from werkzeug.exceptions import Unauthorized

from configs import dify_config
from controllers.common.fields import SimpleResultOptionalDataResponse
from controllers.common.schema import register_response_schema_models, register_schema_models
from controllers.console import console_ns
from controllers.console.auth.error import (
    AuthServiceAuthenticationFailedError,
    AuthServiceConfigurationError as AuthServiceConfigurationHttpError,
)
from controllers.console.wraps import setup_required
from extensions.ext_database import db
from libs.auth_service import (
    AuthServiceClient,
    AuthServiceConfigurationError,
    AuthServiceError,
)
from libs.helper import extract_remote_ip
from libs.token import (
    set_access_token_to_cookie,
    set_csrf_token_to_cookie,
    set_refresh_token_to_cookie,
)
from models.account import Account, AccountStatus, Tenant, TenantAccountRole, TenantStatus
from services.account_service import AccountService, RegisterService, TenantService

logger = logging.getLogger(__name__)


class AuthServiceLoginPayload(BaseModel):
    token: str = Field(..., description="Access token issued by auth-service")


register_schema_models(console_ns, AuthServiceLoginPayload)
register_response_schema_models(console_ns, SimpleResultOptionalDataResponse)


@console_ns.route("/auth-service/login")
class AuthServiceLoginApi(Resource):
    @setup_required
    @console_ns.expect(console_ns.models[AuthServiceLoginPayload.__name__])
    @console_ns.response(200, "Success", console_ns.models[SimpleResultOptionalDataResponse.__name__])
    def post(self):
        payload = AuthServiceLoginPayload.model_validate(console_ns.payload or {})

        try:
            auth_service_client = AuthServiceClient()
            claims = auth_service_client.check_token(payload.token)
            user_info = auth_service_client.get_user_info(payload.token)
        except Unauthorized as exc:
            raise AuthServiceAuthenticationFailedError() from exc
        except AuthServiceConfigurationError as exc:
            raise AuthServiceConfigurationHttpError(str(exc)) from exc
        except AuthServiceError as exc:
            raise AuthServiceConfigurationHttpError(str(exc)) from exc

        tenant = _load_target_workspace()
        external_user_id = _resolve_external_user_id(claims, user_info.user_id)
        if not external_user_id:
            raise AuthServiceAuthenticationFailedError("auth-service token is missing sub.")

        account = _get_or_create_account(
            external_user_id=external_user_id,
            user_name=user_info.user_name,
            email=user_info.email,
        )
        _ensure_workspace_membership(account, tenant)

        token_pair = AccountService.login(account=account, ip_address=extract_remote_ip(request))
        response = make_response({"result": "success"})
        set_access_token_to_cookie(request, response, token_pair.access_token)
        set_refresh_token_to_cookie(request, response, token_pair.refresh_token)
        set_csrf_token_to_cookie(request, response, token_pair.csrf_token)
        return response


def _resolve_external_user_id(claims: dict[str, object], fallback_user_id: str) -> str:
    sub = claims.get("sub")
    return sub if isinstance(sub, str) and sub else fallback_user_id


def _get_or_create_account(*, external_user_id: str, user_name: str, email: str | None) -> Account:
    provider = dify_config.AUTH_SERVICE_PROVIDER
    account = Account.get_by_openid(provider, external_user_id)
    normalized_email = _normalize_email(email, external_user_id)

    if account is None:
        account = AccountService.get_account_by_email_with_case_fallback(normalized_email)

    if account is None:
        account = RegisterService.register(
            email=normalized_email,
            name=_resolve_account_name(user_name, normalized_email),
            open_id=external_user_id,
            provider=provider,
            language="en-US",
            is_setup=True,
            create_workspace_required=False,
        )
    else:
        if account.status == AccountStatus.BANNED:
            raise AuthServiceAuthenticationFailedError("Account is banned.")
        AccountService.link_account_integrate(provider, external_user_id, account)

    return account


def _normalize_email(email: str | None, external_user_id: str) -> str:
    if email:
        return email.lower()
    safe_external_user_id = re.sub(r"[^a-z0-9._-]", "-", external_user_id.lower()).strip("-.")
    if not safe_external_user_id:
        safe_external_user_id = "auth-service-user"
    return f"{safe_external_user_id}@{dify_config.AUTH_SERVICE_FALLBACK_EMAIL_DOMAIN}"


def _resolve_account_name(user_name: str, normalized_email: str) -> str:
    if user_name:
        return user_name
    return normalized_email.split("@", 1)[0]


def _load_target_workspace() -> Tenant:
    workspace_id = dify_config.AUTH_SERVICE_DEFAULT_WORKSPACE_ID
    workspace_role = dify_config.AUTH_SERVICE_DEFAULT_WORKSPACE_ROLE

    if not workspace_id:
        raise AuthServiceConfigurationHttpError("AUTH_SERVICE_DEFAULT_WORKSPACE_ID is not configured")

    if not TenantAccountRole.is_valid_role(workspace_role):
        raise AuthServiceConfigurationHttpError("AUTH_SERVICE_DEFAULT_WORKSPACE_ROLE is invalid")

    tenant = db.session.scalar(
        select(Tenant).where(Tenant.id == workspace_id, Tenant.status == TenantStatus.NORMAL).limit(1)
    )
    if tenant is None:
        raise AuthServiceConfigurationHttpError("Configured auth-service workspace does not exist")

    return tenant


def _ensure_workspace_membership(account: Account, tenant: Tenant) -> None:
    workspace_role = dify_config.AUTH_SERVICE_DEFAULT_WORKSPACE_ROLE

    joined_tenants = TenantService.get_join_tenants(account)
    if all(existing_tenant.id != tenant.id for existing_tenant in joined_tenants):
        TenantService.create_tenant_member(tenant, account, role=workspace_role)

    TenantService.switch_tenant(account, tenant.id)
