import os
import warnings


def get_env_value(key: str, default: str = None) -> str:
    value = os.environ.get(key)

    if value is not None:
        return value

    if default is not None:
        warnings.warn(
            f"Environment variable {key} is not set. Using default: {default}",
            stacklevel=2,
        )
        return default

    raise KeyError(f"Environment variable {key} is not set.")
