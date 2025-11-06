"""
This is a minimal django settings.py file that only includes configs that are necessary
to generate the static site (e.g. no need for DATABASES, LOGIN_URL, etc.).
"""

# you can add your own settings
BASE_URL = "http://localhost:8000"  # used in canonical tags (which need absolute urls) in base.html

# since this project is used to generate a static site, no need for typical wsgi settings
DEBUG = True  # not used, but helpful for troubleshooting
SECRET_KEY = "unused"  # no sessions, so no need for secrets
ALLOWED_HOSTS = ["*"]  # no wsgi server, so no host checking

# add "runcheap_ssg" to the list of installed apps
INSTALLED_APPS = [
    "django.contrib.staticfiles",  # needed to enable static files in templates
    "runcheap_ssg",  # SSG app that adds management commands: `runcheap_ssg_build` and `runcheap_ssg_serve`
    "my_website",  # your website app
]
ROOT_URLCONF = "my_website.urls"  # your website's urls
STATIC_URL = "assets/"  # prefix for {% static "my_logo.png" %} static files in templates

# some middlewares are needed to enable various features
MIDDLEWARE = [
    "django.middleware.locale.LocaleMiddleware",  # needed to enable translations
    "django.middleware.common.CommonMiddleware",  # needed to enable APPEND_SLASH redirects (True by default)
]

# the static site generator uses django's template system for rendering static pages
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                # needed for {% runcheap_ssg_canonical_url %}
                # NOTE: since templates are pre-rendered, don't use {{ request }} attributes for individual requests
                "django.template.context_processors.request",
                # example custom context context_processor
                "my_website.context_processors.my_context",
            ],
        },
    },
]

# the static site generator can render pages in multiple languages
# (you need to specify which languages, otherwise all languages will be rendered)
LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("nl", "Dutch"),
]
