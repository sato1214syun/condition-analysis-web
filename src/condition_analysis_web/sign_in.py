"""Registering users."""

from pathlib import Path
from typing import Any, TypedDict, cast

import streamlit as st
import streamlit_authenticator as st_auth
import tomli_w


class Secrets(TypedDict):  # noqa: D101
    cookie: "_CookieConfigType"
    credentials: "_CredentialsType"
    preauthorized: "_PreauthorizedType"


class _CookieConfigType(TypedDict):
    expiry_days: int
    key: str
    name: str


class _CredentialsType(TypedDict):
    usernames: dict[str, "_UserInfoType"]


class _UserInfoType(TypedDict):
    email: str
    name: str
    password: str


class _PreauthorizedType(TypedDict):
    emails: list[str]


def sign_in() -> None:  # noqa: D103
    secrets_path = Path("./.streamlit/secrets.toml")
    if not st.secrets.load_if_toml_exists():
        secrets_path.parent.mkdir(exist_ok=True)
        secrets = {
            "cookie": {
                "expiry_days": 1,
                "key": "some_signature_key",
                "name": "some_cookie_name",
            },
            "credentials": {"usernames": {}},
            "preauthorized": {"emails": []},
        }
        with secrets_path.open("wb") as f:
            tomli_w.dump(secrets, f)

    # セットアップ
    authenticator = st_auth.Authenticate(
        dict(st.secrets["credentials"]),
        st.secrets["cookie"]["name"],
        st.secrets["cookie"]["key"],
        st.secrets["cookie"]["expiry_days"],
        st.secrets["preauthorized"],
    )
    try:
        (
            email_of_registered_user,
            username_of_registered_user,
            name_of_registered_user,
        ) = authenticator.register_user(pre_authorization=False)
        if email_of_registered_user:
            st.success("User registered successfully")
            with secrets_path.open("wb") as f:
                tomli_w.dump(cast(dict[str, Any], secrets), f)
    except Exception as e:  # noqa: BLE001
        st.error(e)


if __name__ == "__main__":
    sign_in()
