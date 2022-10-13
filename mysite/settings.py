import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "0p6i4zu_vyp3cy8x_(maxhulnl@y%cl)8f5#djv7q^$1^m^w*h"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*", "127.0.0.1", "cogofly.com", "www.cogofly.com", "82.165.179.31"]


# Application definition

INSTALLED_APPS = [
    "dal",
    "dal_select2",
    "cities_light",
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "whitenoise",
    "cogofly",
    "seo",
    "compressor",
    "svg",
    "social_django",
    "languages",
    "captcha",
    "multiselectfield",
    "background_task",
    "django_password_strength",
    "django_dkim",
    'django_crontab',
]

CRONJOBS = [
    (
        '0 0 * * *',
        'django.core.management.call_command',
        ['dumpdata', 'cogofly'], {'indent': 1}, 
        '> /home/cogofly/cogofly2/backups/last_cogofly_db_backup.json',
    ),
    (
        '5 0 * * *',
        'django.core.management.call_command',
        ['dumpdata', 'seo'], {'indent': 2}, 
        '> /home/cogofly/cogofly2/backups/last_seo_db_backup.json',
    ),
    ('10 0 * * *', 'django.core.management.call_command', ['seo_command'], {'indent': 3}),
]


CITIES_LIGHT_APP_NAME = "cogofly"

AUTH_USER_MODEL = "cogofly.User"

AUTHENTICATION_BACKENDS = (
    "social_core.backends.facebook.FacebookOAuth2",
    "social_core.backends.google.GoogleOAuth2",
    "social_core.backends.twitter.TwitterOAuth",
    "social_core.backends.linkedin.LinkedinOAuth2",
    "cogofly.backends.UserBackend",
    "social_core.backends.instagram.InstagramOAuth2",
)

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 9,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

DEFAULT_FROM_EMAIL = "support@cogofly.com"

ADMIN_EMAIL = "cogofly@gmail.com"
WELCOME_EMAIL = "welcome@cogofly.com"
CONTACT_EMAIL = "support@cogofly.com"
ADMIN_CONTACT = "admin@cogofly.com"

EMAIL_BACKEND = "django_dkim.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.ionos.fr"
EMAIL_USE_SSL = True
EMAIL_HOST_USER = "support@cogofly.com"
EMAIL_PORT = 465
EMAIL_HOST_PASSWORD = "Superkakou210673@"
"""
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
SERVER_EMAIL = 'no-reply@cogofly.com'
"""
DKIM_SELECTOR = "1621696512.cogofly"
DKIM_DOMAIN = "cogofly.com"
DKIM_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIICXgIBAAKBgQDdW7nrpEtc9v3MUezFjtWy/S5lVEDXAecDoIUUFv0cuDTkeb3P
BylPcJwCtvqCsMgDxcczg30dgt8sm9xFGCQP2mgfH8rpH1xjdq74to3AGgFxPcos
0KdDfco73Z3EO80uJjzKFMzfaX2R42MU5vCKaWNjTKto5FttcEpa/dKy4wIDAQAB
AoGBAITJi6RR8GuaNvGki5aPcp5mxrg+bI8OMxi36Fz+1WOvFPuiFDznHN7svInc
Xjab+cBZmn/KdvmHEn3eGarRKn/COnLEOGQCwOfdVNCgCtj0tJbEVf5WPyqBdpqi
Eeo5cDB7j4QTJZRSoMpF20zBGtuvFCtCQcds5+T/V9nHSxoBAkEA+AqHPqcSX8A/
FAWuvkDjXZAJ/KwsXCu1o8gCHL95q/8XHLYL7IEuIH28W4boEULtKMg4c5ZtG9K0
ls+vE5XagQJBAOR2BMNpxdLdkUJR47fP4jjK+zuQdanhsPwIDzb5OLyq9BjhgUGC
2ZClhjoxC1lYxmgUsvcbZ/a+zwUuFkGXs2MCQQCtEauMa8bGSL26mrxyw5PhlL9j
Lj9FkLoMrWHL7U5YVIUr41oui3RD93eV5WvHn4sbCZlaDXvUDhEzqXXflJABAkA9
epTlkT0u9Xj1g9vnxwV1iwn4iXNgd9+Msw6FGKPwAYEWgPirjG7HwgNQ/Ym0TXN2
5rsSTEm52LcVCcXreMtJAkEApY3lySYyNQ+7eZqa95dI5yn73GG2q3Tqekps8Gu7
nstyxJZ6XEyGDyjjkkwFdJQUdjI5bOzjJ9RPDvbdyNkFzw==
-----END RSA PRIVATE KEY-----"""

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"

RECAPTCHA_PRIVATE_KEY = "6LeCEakZAAAAAIP3BHYOwQn36I1wFkTLJR5sI7TP"
RECAPTCHA_PUBLIC_KEY = "6LeCEakZAAAAAIFB4JyQUhPXpd42Fq5I3LY2cxMz"

SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
SOCIAL_AUTH_USER_MODEL = "cogofly.User"

SOCIAL_AUTH_NEW_USER_REDIRECT_URL = "/signup/next"

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "cogofly.activate_user.associate_by_email",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)


SOCIAL_AUTH_FACEBOOK_KEY = "285064706949391"
SOCIAL_AUTH_FACEBOOK_SECRET = "369df6f3a43decd80a0014bdba2e1a4b"

SOCIAL_AUTH_FACEBOOK_SCOPE = ["email"]
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    "fields": "id, name, email, age_range",
}
SOCIAL_AUTH_FACEBOOK_EXTRA_DATA = ["name"]

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = (
    "264525966015-orq8eiuh15eqsd7i79fo0106hvs0vo0r.apps.googleusercontent.com"
)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = "ZLPGIynNkZfm-YQzuRTKEm86"

SOCIAL_AUTH_LINKEDIN_OAUTH2_KEY = "77oisp55mgsvlt"
SOCIAL_AUTH_LINKEDIN_OAUTH2_SECRET = "xG5lKaF6ZBmP52ah"
SOCIAL_AUTH_LINKEDIN_OAUTH2_SCOPE = ["r_emailaddress"]
SOCIAL_AUTH_LINKEDIN_OAUTH2_FIELD_SELECTORS = ["emailAddress"]

"""SOCIAL_AUTH_INSTAGRAM_KEY = '474178067636932'
SOCIAL_AUTH_INSTAGRAM_SECRET = '4c3b0c392a4939a9bccf11eabbe941c2'
SOCIAL_AUTH_INSTAGRAM_SCOPE = ['email']
SOCIAL_AUTH_INSTAGRAM_PROFILE_EXTRA_PARAMS = {
  'fields': 'id, email'
}
SOCIAL_AUTH_INSTAGRAM_EXTRA_DATA = [
    ('email', 'email')
]"""


SOCIAL_AUTH_TWITTER_KEY = "SaRP86bVG5TSUAFTvVgo80kqz"
SOCIAL_AUTH_TWITTER_SECRET = "uTPNJTXj0woQYLJWntLgwYUSyVjj1eDtpzzSWBkwWHMlFGCjul"
SOCIAL_AUTH_TWITTER_SCOPE = ["email"]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "cogofly.middleware.TimezoneMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
]

ROOT_URLCONF = "mysite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
        },
    },
]

WSGI_APPLICATION = "mysite.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'cogofly',
        'USER': 'cogofly',
        'PASSWORD': 'cogofly_admin',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
"""
# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/fr/1.8/topics/i18n/

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True
_ = lambda s: s

DATE_INPUT_FORMATS = ("%Y-%m-%d",)

LANGUAGES = (
    ("en", "English"),
    # ('fr', 'French'),
    # ('hi', 'Hindi'),
    # ('ch', _('Chinese')),
    # ('es', 'Spanish'),
    # ('de', 'German'),
    # ('it', 'Italian'),
    # ('pt', 'Portuguese'),
    # ('ru', 'Russian'),
    # ('ja', 'Japanese'),
    # ('ko', 'Korean'),
    # ('vi', 'Vietnamese'),
)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

import mimetypes

mimetypes.add_type("text/css", ".css", True)

STATIC_URL = "/static/"
STATIC_ROOT = "static"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = "media"

LOCALE_PATHS = ("locale",)

COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
    "compressor.finders.CompressorFinder",
)
""" 
COMPRESS_CSS_FILTERS = (
    'compressor.filters.css_default.CssAbsoluteFilter',
    'django_compressor_autoprefixer.AutoprefixerFilter',
    'compressor.filters.cssmin.rCSSMinFilter'
)
COMPRESS_AUTOPREFIXER_ARGS = '--no-map --use autoprefixer'
"""

CITIES_LIGHT_TRANSLATION_LANGUAGES = [
    "fr",
    "en",
    "hi",
    "es",
    "de",
    "it",
    "pt",
    "ru",
    "ja",
    "ko",
    "vi",
]
CITIES_LIGHT_CITY_SOURCES = ["http://download.geonames.org/export/dump/cities500.zip"]

LOGGING = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {"logger": {"handlers": ["console"]}},
}

JAZZMIN_SETTINGS = {
    "site_title": "CoGoFly",
    "site_header": "CoGoFly",
    "site_logo": "../static/img/cogofly_logo_v2-cropped-white.png",
    "welcome_sign": "Welcome to the CoGoFly administration",
    "copyright": "CoGoFly",
}
