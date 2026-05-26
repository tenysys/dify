from pydantic import Field
from pydantic_settings import BaseSettings


class AuthServiceConfig(BaseSettings):
    """
    Configuration settings for auth-service console SSO integration.
    """

    AUTH_SERVICE_ENABLED: bool = Field(
        description="Enable auth-service token exchange for Dify console login.",
        default=False,
    )

    AUTH_SERVICE_PROVIDER: str = Field(
        description="Provider name used for AccountIntegrate binding.",
        default="auth-service",
    )

    AUTH_SERVICE_CHECK_TOKEN_URL: str | None = Field(
        description="Full auth-service check_token endpoint URL.",
        default=None,
    )

    AUTH_SERVICE_USER_INFO_URL: str | None = Field(
        description="Full auth-service user info endpoint URL.",
        default=None,
    )

    AUTH_SERVICE_REQUEST_TIMEOUT: float = Field(
        description="Timeout in seconds for auth-service HTTP requests.",
        default=10.0,
        gt=0,
    )

    AUTH_SERVICE_DEFAULT_WORKSPACE_ID: str | None = Field(
        description="Workspace ID that first-time auth-service users will join.",
        default=None,
    )

    AUTH_SERVICE_DEFAULT_WORKSPACE_ROLE: str = Field(
        description="Workspace role assigned to first-time auth-service users.",
        default="normal",
    )

    AUTH_SERVICE_FALLBACK_EMAIL_DOMAIN: str = Field(
        description="Fallback email domain used when auth-service user info has no email.",
        default="auth-service.local",
    )
