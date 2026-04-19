import os


def get_env_file() -> str:
    app_mode = os.environ.get("APP_MODE", "prod")
    env_file_prefix = f"-{app_mode}" if app_mode != "prod" else ""
    return f".env{env_file_prefix}"
