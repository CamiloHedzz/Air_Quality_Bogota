"""Configuración de desarrollo local con una base SQLite independiente."""

from .settings import *  # noqa: F403


LOCAL_DATA_DIR = BASE_DIR / ".local"
LOCAL_DATA_DIR.mkdir(exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": LOCAL_DATA_DIR / "db.sqlite3",
    }
}
