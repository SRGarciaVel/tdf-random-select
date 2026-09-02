from unittest.mock import MagicMock, patch

import pytest
import requests

from backend.app.services.player_profile_service import (
    PlayerProfileUnavailable,
    fetch_player_profile,
)


def _fake_response(status_code: int, json_data: dict | None = None) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    return response


def test_fetch_player_profile_returns_json_on_success() -> None:
    fake = _fake_response(
        200,
        {
            "cfn_id": "1733837998",
            "display_name": "AckermanFG",
            "league_rank": "Master",
            "league_points": 1200,
            "master_rating": 1600,
            "character_name": "Cammy",
        },
    )
    with patch(
        "backend.app.services.player_profile_service.requests.get",
        return_value=fake,
    ) as mock_get:
        result = fetch_player_profile("1733837998")

    assert result["character_name"] == "Cammy"
    assert result["master_rating"] == 1600
    called_url = mock_get.call_args[0][0]
    assert "1733837998" in called_url


def test_fetch_player_profile_raises_on_404() -> None:
    fake = _fake_response(404)
    with patch(
        "backend.app.services.player_profile_service.requests.get",
        return_value=fake,
    ):
        with pytest.raises(PlayerProfileUnavailable):
            fetch_player_profile("0000000000")


def test_fetch_player_profile_raises_on_network_error() -> None:
    with patch(
        "backend.app.services.player_profile_service.requests.get",
        side_effect=requests.ConnectionError("no hay red"),
    ):
        with pytest.raises(PlayerProfileUnavailable):
            fetch_player_profile("1733837998")


def test_fetch_player_profile_raises_on_unexpected_status() -> None:
    fake = _fake_response(500)
    with patch(
        "backend.app.services.player_profile_service.requests.get",
        return_value=fake,
    ):
        with pytest.raises(PlayerProfileUnavailable):
            fetch_player_profile("1733837998")
