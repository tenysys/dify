from unittest.mock import MagicMock, patch

from libs.auth_service import AUTH_SERVICE_USER_INFO_REQUEST, AuthServiceClient


@patch("libs.auth_service._http_client.post", autospec=True)
def test_get_user_info_uses_auth_service_expected_request_payload(mock_post):
    response = MagicMock()
    response.json.return_value = {
        "code": "2020",
        "data": {
            "email": "admin@nrec.com",
            "userId": "40a21660947c44a6a40030109214f313",
            "userName": "web",
        },
        "id": "0",
        "msg": "OK",
        "succ": True,
        "timestamp": 1780403875448,
    }
    mock_post.return_value = response

    with (
        patch("libs.auth_service.dify_config.AUTH_SERVICE_ENABLED", True),
        patch("libs.auth_service.dify_config.AUTH_SERVICE_CHECK_TOKEN_URL", "http://auth-service/oauth/check_token"),
        patch("libs.auth_service.dify_config.AUTH_SERVICE_USER_INFO_URL", "http://auth-service/auth/info"),
        patch("libs.auth_service.dify_config.AUTH_SERVICE_REQUEST_TIMEOUT", 10),
    ):
        client = AuthServiceClient()

        user_info = client.get_user_info("test-token")

    assert user_info.user_id == "40a21660947c44a6a40030109214f313"
    assert user_info.user_name == "web"
    assert user_info.email == "admin@nrec.com"
    mock_post.assert_called_once_with(
        "http://auth-service/auth/info",
        headers={"Authorization": "Bearer test-token"},
        json=AUTH_SERVICE_USER_INFO_REQUEST,
        timeout=10,
    )
