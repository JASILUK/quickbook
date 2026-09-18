from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticate requests using the access JWT
    stored in an HttpOnly cookie.
    """

    def authenticate(self, request):
        access_token = request.COOKIES.get(
            "access_token"
        )

        if not access_token:
            return None

        validated_token = self.get_validated_token(
            access_token
        )

        user = self.get_user(validated_token)

        if not user.is_active:
            raise AuthenticationFailed(
                "This account is inactive."
            )

        return user, validated_token