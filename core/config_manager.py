import os
from ast import literal_eval
from importlib import import_module


class Config:
    API_ID = 0
    API_HASH = ""
    BOT_TOKEN = ""
    PORT = 8080
    OWNER_ID = 0
    DATABASE_URL = ""
    LOG_CHANNEL = []

    @classmethod
    def get(cls, key):
        return getattr(cls, key) if hasattr(cls, key) else None

    @classmethod
    def set(cls, key, value):
        if hasattr(cls, key):
            value = cls.convert(key, value)
            setattr(cls, key, value)
        else:
            raise KeyError(f"{key} is not a valid configuration key.")

    @classmethod
    def get_all(cls):
        return {
            key: getattr(cls, key)
            for key in cls.__dict__
            if not key.startswith("__")
            and not callable(getattr(cls, key))
        }

    @classmethod
    def load(cls):
        cls.load_config()
        cls.load_env()

    @classmethod
    def load_config(cls):
        try:
            settings = import_module("config")
        except ModuleNotFoundError:
            return

        for key in cls.get_all():
            if not hasattr(settings, key):
                continue

            value = getattr(settings, key)

            if value in ("", None, [], {}):
                continue

            cls.set(key, value)

    @classmethod
    def load_env(cls):
        for key in cls.get_all():
            value = os.getenv(key)

            if value is not None:
                cls.set(key, value)

    @classmethod
    def convert(cls, key, value):
        current = getattr(cls, key)

        if isinstance(current, bool):
            if isinstance(value, bool):
                return value

            return str(value).lower() in (
                "true",
                "1",
                "yes",
                "on",
            )

        if isinstance(current, int):
            try:
                return int(value)
            except (ValueError, TypeError):
                return current

        if isinstance(current, float):
            try:
                return float(value)
            except (ValueError, TypeError):
                return current

        if isinstance(current, list):
            if isinstance(value, list):
                return value

            if isinstance(value, str):
                try:
                    parsed = literal_eval(value)

                    if isinstance(parsed, list):
                        return parsed
                except (ValueError, SyntaxError):
                    pass

                return [
                    item.strip()
                    for item in value.split(",")
                    if item.strip()
                ]

        if isinstance(current, dict):
            if isinstance(value, dict):
                return value

            if isinstance(value, str):
                try:
                    parsed = literal_eval(value)

                    if isinstance(parsed, dict):
                        return parsed
                except (ValueError, SyntaxError):
                    pass

        return value

    @classmethod
    def load_dict(cls, data):
        for key, value in data.items():
            if hasattr(cls, key):
                cls.set(key, value)


Config.load()
