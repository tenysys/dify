from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import httpx
from pydantic import TypeAdapter
from werkzeug.exceptions import Unauthorized

from configs import dify_config
from core.helper.http_client_pooling import get_pooled_http_client

logger = logging.getLogger(__name__)

type JsonObject = dict[str, Any]

JSON_OBJECT_ADAPTER: TypeAdapter[JsonObject] = TypeAdapter(JsonObject)

_http_client: httpx.Client = get_pooled_http_client(
    "auth-service:default",
    lambda: httpx.Client(limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)),
)


@dataclass
class AuthServiceUserInfo:
    user_id: str
    user_name: str
    email: str | None


class AuthServiceError(Exception):
    pass


class AuthServiceConfigurationError(AuthServiceError):
    pass


class AuthServiceClient:
    def __init__(self) -> None:
        if not dify_config.AUTH_SERVICE_ENABLED:
            raise AuthServiceConfigurationError("auth-service login is disabled")
        if not dify_config.AUTH_SERVICE_CHECK_TOKEN_URL:
            raise AuthServiceConfigurationError("AUTH_SERVICE_CHECK_TOKEN_URL is not configured")
        if not dify_config.AUTH_SERVICE_USER_INFO_URL:
            raise AuthServiceConfigurationError("AUTH_SERVICE_USER_INFO_URL is not configured")

        self._check_token_url = dify_config.AUTH_SERVICE_CHECK_TOKEN_URL
        self._user_info_url = dify_config.AUTH_SERVICE_USER_INFO_URL
        self._timeout = dify_config.AUTH_SERVICE_REQUEST_TIMEOUT

    def check_token(self, token: str) -> JsonObject:
        try:
            response = _http_client.post(
                self._check_token_url,
                params={"token": token},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = JSON_OBJECT_ADAPTER.validate_python(response.json())
        except httpx.HTTPStatusError as exc:
            logger.warning("auth-service check_token rejected token: %s", exc)
            raise Unauthorized("Invalid auth-service token.") from exc
        except (httpx.HTTPError, ValueError) as exc:
            logger.exception("auth-service check_token request failed")
            raise AuthServiceError("auth-service token validation failed") from exc

        if not payload.get("active", True):
            raise Unauthorized("Invalid auth-service token.")

        return payload

    def get_user_info(self, token: str) -> AuthServiceUserInfo:
        try:
            response = _http_client.post(
                self._user_info_url,
                headers={"Authorization": f"Bearer {token}"},
                json={"id": "dify", "body": {}},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = JSON_OBJECT_ADAPTER.validate_python(response.json())
        except httpx.HTTPStatusError as exc:
            logger.warning("auth-service auth/info rejected token: %s", exc)
            raise Unauthorized("Invalid auth-service token.") from exc
        except (httpx.HTTPError, ValueError) as exc:
            logger.exception("auth-service auth/info request failed")
            raise AuthServiceError("auth-service user info lookup failed") from exc

        data = payload.get("data")
        if not isinstance(data, dict):
            if "userId" in payload or "userName" in payload:
                data = payload
            else:
                raise AuthServiceError("auth-service user info response is malformed")

        user_id = data.get("userId")
        user_name = data.get("userName")
        email = data.get("email")

        if not isinstance(user_id, str) or not user_id:
            raise AuthServiceError("auth-service user info is missing userId")

        return AuthServiceUserInfo(
            user_id=user_id,
            user_name=user_name if isinstance(user_name, str) else "",
            email=email if isinstance(email, str) and email else None,
        )
