import json
from unittest.mock import MagicMock, patch

import pytest

from bingo_generator.generator import generate_phrases

MOCK_MISTRAL_PATH = "bingo_generator.generator.Mistral"


@patch(MOCK_MISTRAL_PATH)
def test_generate_phrases_returns_correct_count(mock_mistral_cls):
    mock_client = MagicMock()
    mock_mistral_cls.return_value = mock_client
    phrases = ["phrase one", "phrase two", "phrase three"]
    mock_client.chat.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(phrases)))]
    )

    result = generate_phrases("introvert", count=3, model="mistral-large-latest")
    assert len(result) == 3
    assert result[0] == "phrase one"


@patch(MOCK_MISTRAL_PATH)
def test_generate_phrases_language_hint(mock_mistral_cls):
    mock_client = MagicMock()
    mock_mistral_cls.return_value = mock_client
    mock_client.chat.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(["а", "б"])))]
    )

    generate_phrases(
        "социофоб", count=2, model="mistral-large-latest", lang_hint="Russian"
    )

    call_args = mock_client.chat.complete.call_args
    prompt = call_args[1]["messages"][1]["content"]
    assert "Russian" in prompt


@patch(MOCK_MISTRAL_PATH)
def test_generate_phrases_truncates_to_count(mock_mistral_cls):
    mock_client = MagicMock()
    mock_mistral_cls.return_value = mock_client
    phrases = ["a", "b", "c", "d", "e"]
    mock_client.chat.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(phrases)))]
    )

    result = generate_phrases("topic", count=3, model="mistral-large-latest")
    assert len(result) == 3


@patch(MOCK_MISTRAL_PATH)
def test_generate_phrases_uses_api_key(mock_mistral_cls):
    mock_client = MagicMock()
    mock_mistral_cls.return_value = mock_client
    mock_client.chat.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(["x"])))]
    )

    generate_phrases("topic", count=1, model="mistral-large-latest", api_key="test-key")
    mock_mistral_cls.assert_called_once_with(api_key="test-key")


@patch(MOCK_MISTRAL_PATH)
def test_generate_phrases_auto_detects_cyrillic(mock_mistral_cls):
    mock_client = MagicMock()
    mock_mistral_cls.return_value = mock_client
    mock_client.chat.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(["да"])))]
    )

    generate_phrases("интроверт", count=1, model="mistral-large-latest")
    call_args = mock_client.chat.complete.call_args
    prompt = call_args[1]["messages"][1]["content"]
    assert "Russian" in prompt


@patch(MOCK_MISTRAL_PATH)
def test_generate_phrases_raises_on_non_list(mock_mistral_cls):
    mock_client = MagicMock()
    mock_mistral_cls.return_value = mock_client
    mock_client.chat.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps({"key": "value"})))]
    )

    with pytest.raises(ValueError, match="Expected a JSON array"):
        generate_phrases("topic", count=1, model="mistral-large-latest")
