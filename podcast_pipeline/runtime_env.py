from __future__ import annotations

import os


def _read_windows_user_env(name: str) -> str | None:
    if os.name != "nt":
        return None
    try:
        import winreg
    except ImportError:
        return None

    for root, subkey in (
        (winreg.HKEY_CURRENT_USER, r"Environment"),
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
    ):
        try:
            with winreg.OpenKey(root, subkey) as key:
                value, _ = winreg.QueryValueEx(key, name)
                return os.path.expandvars(str(value))
        except OSError:
            continue
    return None


def get_env_value(name: str) -> str | None:
    return os.getenv(name) or _read_windows_user_env(name)
