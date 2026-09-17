import os

from scheduler.types import Broker, SchedulerConfiguration


def gettext(s):
    return s


def _(x):
    return x


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DEBUG = True

ADMINS = [
    ("Marco", "marco@cruncher.ch"),
]

MANAGERS = ADMINS
LANGUAGES = [
    ("en", _("English")),
    ("de", _("German")),
    ("fr", _("French")),
    ("it", _("Italian")),
]


DEFAULT_LANGUAGE = 0

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "hoard",
    }
}


ALLOWED_HOSTS = [
    ".cruncher.ch",
    ".test.cruncher.ch",
    ".hoard.ch",
    "127.0.0.1",
    "0.0.0.0",
    "testserver",
]


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379",
        "KEY_PREFIX": "hoard",
    }
}

TIME_ZONE = "Europe/Zurich"
LANGUAGE_CODE = "en"
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True

# INTERNAL_IPS = ('127.0.0.1', )
INTERNAL_IPS = []

MEDIA_ROOT = os.path.join(BASE_DIR, "..", "tmp", "media")
STATIC_ROOT = os.path.join(BASE_DIR, "..", "tmp", "static")
MEDIA_URL = "/media/"
STATIC_URL = "/static/"
ADMIN_MEDIA_PREFIX = "/static/admin/"
DEV_STATIC_URLS = {}


STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)


STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

THUMBNAIL_DEFAULT_STORAGE = "easy_thumbnails.storage.ThumbnailFileSystemStorage"
THUMBNAIL_ALIASES = {
    "": {
        # "team-member": {"size": (1200, 900), "crop": True, "upscale": True},
    }
}


SECRET_KEY = "unsecure-secret-key"
TEST_RUNNER = "django.test.runner.DiscoverRunner"


# TEMPLATE_DIRS = (
#     os.path.join(BASE_DIR, 'templates'),
# )

LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)


ROOT_URLCONF = "hoard.urls"
AUTH_USER_MODEL = "users.User"


# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = "hoard.wsgi.application"


INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.forms",
    "apps.users",
    "apps.hoarder",
    "apps.cruncher",
    "gunicorn",
    "django_extensions",
    "storages",
    "django_otp",
    # https://django-otp-official.readthedocs.io/en/stable/overview.html#plugins-and-devices
    "django_otp.plugins.otp_totp",
    # "django_otp.plugins.otp_hotp",
    # "django_otp.plugins.otp_email",
    "django_otp.plugins.otp_static",
    # SMS: https://django-otp-twilio.readthedocs.io/en/latest/
    "scheduler",
)


META_SITE_PROTOCOL = "https"
META_SITE_DOMAIN = "hoard.ch"
META_USE_OG_PROPERTIES = True
META_SITE_TYPE = "website"

PAGE_META_DESCRIPTION_LENGTH = 160


THUMBNAIL_PROCESSORS = (
    "easy_thumbnails.processors.colorspace",
    "easy_thumbnails.processors.autocrop",
    "filer.thumbnail_processors.scale_and_crop_with_subject_location",
    "easy_thumbnails.processors.filters",
)
INTERNAL_IPS = []

MIDDLEWARE = (
    # 'django.middleware.cache.UpdateCacheMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # 'django.middleware.cache.FetchFromCacheMiddleware',
)


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(PROJECT_DIR, "..", "templates")],
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.request",
                "django.template.context_processors.media",
                "django.template.context_processors.debug",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "sekizai.context_processors.sekizai",
            ],
            "debug": False,
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                ),
            ],
        },
    }
]

FILER_CANONICAL_URL = "c/"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "apps.cruncher.auth_backends.EmailBackend",
)


FILE_UPLOAD_PERMISSIONS = 0o644

BASE_URL = "https://hoard.mbi.me"


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.


def suppress_allowed_hosts(record):
    from django.core.exceptions import DisallowedHost, SuspiciousOperation

    if record.exc_info:
        exc_value = record.exc_info[1]
        if isinstance(exc_value, SuspiciousOperation):
            return False
        if isinstance(exc_value, DisallowedHost):
            return False
    return True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
        "suppress_allowed_hosts": {
            "()": "django.utils.log.CallbackFilter",
            "callback": suppress_allowed_hosts,
        },
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false", "suppress_allowed_hosts"],
            "class": "django.utils.log.AdminEmailHandler",
        }
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        }
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


# Set your DSN value
RAVEN_CONFIG = {"dsn": None}

SCHEDULER_CONFIG = SchedulerConfiguration(
    EXECUTIONS_IN_PAGE=20,
    SCHEDULER_INTERVAL=10,
    BROKER=Broker.REDIS,
    # Callback timeout in seconds (success/failure/stopped)
    CALLBACK_TIMEOUT=60,
    # Default values, can be overriden per task/job
    # Time To Live (TTL) in seconds to keep successful job results
    DEFAULT_SUCCESS_TTL=3600,
    DEFAULT_FAILURE_TTL=365
    * 24
    * 60
    * 60,  # Time To Live (TTL) in seconds to keep job failure information
    DEFAULT_JOB_TTL=10 * 60,  # Time To Live (TTL) in seconds to keep job information
    DEFAULT_JOB_TIMEOUT=5 * 60,  # timeout (seconds) for a job
    # General configuration values
    # Time To Live (TTL) in seconds to keep worker information after last heartbeat
    DEFAULT_WORKER_TTL=10 * 60,
    # The interval to run maintenance tasks in seconds. 10 minutes.
    DEFAULT_MAINTENANCE_TASK_INTERVAL=10 * 60,
    DEFAULT_JOB_MONITORING_INTERVAL=30,  # The interval to monitor jobs in seconds.
    # Period (secs) to wait before requiring to reacquire locks
    SCHEDULER_FALLBACK_PERIOD_SECS=120,
)

SCHEDULER_REDIS_DB = 0
SCHEDULER_QUEUES = {"default": {"URL": f"redis://localhost:6379/{SCHEDULER_REDIS_DB}"}}

SHELL_PLUS = "ipython"
