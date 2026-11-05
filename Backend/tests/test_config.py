import os
from unittest.mock import patch

import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            '["https://frontend.example","https://admin.example"]',
            ["https://frontend.example", "https://admin.example"],
        ),
        (
            "https://frontend.example, https://admin.example",
            ["https://frontend.example", "https://admin.example"],
        ),
        ("https://frontend.example", ["https://frontend.example"]),
        ("", []),
    ],
)
def test_cors_origins_accept_json_and_comma_separated_environment_values(
    value: str,
    expected: list[str],
):
    with patch.dict(os.environ, {"CORS_ORIGINS": value}):
        settings = Settings(_env_file=None)

    assert settings.cors_origins == expected


def test_cors_origins_reject_malformed_json_array_with_actionable_error():
    with patch.dict(os.environ, {"CORS_ORIGINS": '["https://frontend.example"'}):
        with pytest.raises(ValueError, match="CORS_ORIGINS must be a JSON array"):
            Settings(_env_file=None)
