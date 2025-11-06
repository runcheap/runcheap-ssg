from django.conf import settings


def my_context(request):
    return {
        "BASE_URL": settings.BASE_URL,
        "LANGUAGE_COOKIE_NAME": settings.LANGUAGE_COOKIE_NAME,
        "LANGUAGE_COOKIE_SECURE": settings.LANGUAGE_COOKIE_SECURE,
        "LANGUAGE_COOKIE_PATH": settings.LANGUAGE_COOKIE_PATH,
        "LANGUAGE_COOKIE_DOMAIN": settings.LANGUAGE_COOKIE_DOMAIN,
        "LANGUAGE_COOKIE_AGE": settings.LANGUAGE_COOKIE_AGE,
        "LANGUAGE_COOKIE_HTTPONLY": settings.LANGUAGE_COOKIE_HTTPONLY,
    }
