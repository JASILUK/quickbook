from django.conf import settings
from django.http import HttpResponse


ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"

AUTH_COOKIE_PATH = "/api/auth/"


def set_auth_cookies(
    response: HttpResponse,
    *,
    access_token: str,
    refresh_token: str,
) -> None:
    """
    Set access and refresh JWT cookies.

    Access token:
        Available to the whole application.

    Refresh token:
        Available only under /api/auth/.
        This allows both refresh and logout endpoints
        to receive the refresh token.
    """

    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        max_age=15 * 60,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        path="/",
    )

    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=7 * 24 * 60 * 60,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        path=AUTH_COOKIE_PATH,
    )


def clear_auth_cookies(
    response: HttpResponse,
) -> None:
    """
    Remove authentication cookies.
    """

    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        path="/",
    )

    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        path=AUTH_COOKIE_PATH,
    )

