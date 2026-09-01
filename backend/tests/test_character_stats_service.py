from unittest.mock import MagicMock, patch

import pytest
import requests

from backend.app.services.character_stats_service import (
    CharacterStatsUnavailable,
    fetch_character_stats,
    warm_up_tdf_edeportes,
)


def _fake_response(status_code: int, json_data: dict | None = None) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    return response


def test_fetch_character_stats_returns_json_on_success() -> None:
    fake = _fake_response(
        200,
        {
            "cfn_id": "1733837998",
            "character_name": "Chun-Li",
            "matches_played": 3643,
            "win_rate": 0.6544,
            "ever_played": True,
        },
    )
    with patch(
        "backend.app.services.character_stats_service.requests.get",
        return_value=fake,
    ) as mock_get:
        result = fetch_character_stats("1733837998", "Chun-Li")

    assert result["ever_played"] is True
    assert result["matches_played"] == 3643
    mock_get.assert_called_once()
    called_url = mock_get.call_args[0][0]
    assert "1733837998" in called_url
    assert "Chun-Li" in called_url


def test_fetch_character_stats_raises_on_404() -> None:
    fake = _fake_response(404)
    with patch(
        "backend.app.services.character_stats_service.requests.get",
        return_value=fake,
    ):
        with pytest.raises(CharacterStatsUnavailable):
            fetch_character_stats("0000000000", "Ryu")


def test_fetch_character_stats_raises_on_network_error() -> None:
    with patch(
        "backend.app.services.character_stats_service.requests.get",
        side_effect=requests.ConnectionError("no hay red"),
    ):
        with pytest.raises(CharacterStatsUnavailable):
            fetch_character_stats("1733837998", "Ryu")


def test_fetch_character_stats_raises_on_unexpected_status() -> None:
    fake = _fake_response(500)
    with patch(
        "backend.app.services.character_stats_service.requests.get",
        return_value=fake,
    ):
        with pytest.raises(CharacterStatsUnavailable):
            fetch_character_stats("1733837998", "Ryu")


def test_warm_up_never_raises_even_on_failure() -> None:
    """El ping de precarga es fire-and-forget - un fallo de red no debe
    propagar ninguna excepción (lo llama un QTimer de fondo, nunca debe
    poder tumbar la app)."""
    with patch(
        "backend.app.services.character_stats_service.requests.get",
        side_effect=requests.ConnectionError("no hay red"),
    ):
        warm_up_tdf_edeportes()  # no debe lanzar nada


def test_warm_up_calls_the_expected_url() -> None:
    fake = _fake_response(200, [])
    with patch(
        "backend.app.services.character_stats_service.requests.get",
        return_value=fake,
    ) as mock_get:
        warm_up_tdf_edeportes()

    called_url = mock_get.call_args[0][0]
    assert "tdf-edeportes-backend.onrender.com" in called_url
