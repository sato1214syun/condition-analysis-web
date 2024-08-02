"""Registering users."""

import tomllib
from pathlib import Path

import streamlit as st
import streamlit_authenticator as st_auth
import tomli_w


def sign_in() -> None:  # noqa: D103
    secrets_path = Path("./.streamlit/secrets.toml")
    if secrets_path.exists():
        with secrets_path.open("rb") as f:
            secrets = tomllib.load(f)

    if not secrets_path.exists() or secrets.get("credentials") is None:
        secrets_path.parent.mkdir(exist_ok=True)
        secrets = {
            "cookie": {
                "expiry_days": 30,
                "key": "some_signature_key",
                "name": "some_cookie_name",
            },
            "credentials": {"usernames": {}},
            "preauthorized": {"emails": []},
        }

    # セットアップ
    authenticator = st_auth.Authenticate(
        secrets["credentials"],
        secrets["cookie"]["name"],
        secrets["cookie"]["key"],
        secrets["cookie"]["expiry_days"],
        secrets["preauthorized"],
    )
    try:
        (
            email_of_registered_user,
            username_of_registered_user,
            name_of_registered_user,
        ) = authenticator.register_user(pre_authorization=False)
        if email_of_registered_user:
            st.success("User registered successfully")
            if secrets.get("credentials") is not None:
                with secrets_path.open("wb") as f:
                    tomli_w.dump(secrets, f)
    except Exception as e:  # noqa: BLE001
        st.error(e)


if __name__ == "__main__":
    sign_in()
