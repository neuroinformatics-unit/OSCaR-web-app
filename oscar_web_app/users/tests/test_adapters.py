from http import HTTPStatus

import pytest
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.models import SocialLogin
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.urls import reverse

from oscar_web_app.users.adapters import SocialAccountAdapter


@pytest.fixture
def login_request(rf):
    request = rf.get("/accounts/oidc/microsoft/login/callback/")
    request.session = {}
    request._messages = FallbackStorage(request)  # noqa: SLF001

    return request


@pytest.mark.parametrize(
    "extra_data",
    [
        pytest.param({}, id="No id token"),
        pytest.param(
            {
                "id_token": {
                    "roles": [],
                },
            },
            id="Id token with no role",
        ),
        pytest.param(
            {
                "id_token": {
                    "roles": ["INVALID-ROLE"],
                },
            },
            id="Id token with wrong role",
        ),
    ],
)
def test_reject_invalid_role(login_request, extra_data, settings):
    """
    Test that login attempts that don't provide the required role are rejected.
    """

    settings.REQUIRED_APP_ROLE = "VALID-ROLE"
    sociallogin = SocialLogin(account=SocialAccount(extra_data=extra_data))
    adapter = SocialAccountAdapter()

    with pytest.raises(ImmediateHttpResponse) as exc_info:
        adapter.pre_social_login(login_request, sociallogin)

    response = exc_info.value.response
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("account_login")

    messages = list(get_messages(login_request))
    assert str(messages[0]) == "You are not authorised to use this application."


@pytest.mark.parametrize(
    "required_app_role",
    [
        pytest.param("", id="No required role"),
        pytest.param("VALID-ROLE", id="Required role provided"),
    ],
)
def test_accept_valid_role(login_request, settings, required_app_role):
    """Test that login attempts that match the required role are accepted."""

    settings.REQUIRED_APP_ROLE = required_app_role
    sociallogin = SocialLogin(
        account=SocialAccount(
            extra_data={
                "id_token": {
                    "roles": ["VALID-ROLE"],
                },
            },
        )
    )
    adapter = SocialAccountAdapter()
    adapter.pre_social_login(login_request, sociallogin)
