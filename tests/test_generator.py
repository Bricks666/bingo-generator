import json
import pytest
from unittest.mock import patch, MagicMock
from bingo_generator.generator import generate_phrases


@patch("bingo_generator.generator.Mistral")
def test_generate_phrases_returns_correct_count(MockMistral):
    mock_client = MagicMock()
    MockMistral.return_value = mock_client
    phrases = ["phrase one", "phrase two", "phrase three"]
    mock_client.chat.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(phrases)))]
    )

    result = generate_phrases("introvert", count=3, model="mistral-large-latest")
    assert len(result) == 3
    assert result[0] == "phrase one"


@patch("bingo_generator.generator.Mistral")
def test_generate_phrases_language_hint(MockMistral):
    mock_client = MagicMock()
    MockMistral.return_value = mock_client
    mock_client.chat.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(["а", "б"])))]
    )

    generate_phrases("социофоб", count=2, model="mistral-large-latest", lang_hint="Russian")

    call_args = mock_client.chat.complete.call_args
    prompt = call_args[1]["messages"][1]["content"]
    assert "Russian" in prompt


@patch("bingo_generator.generator.Mistral")
def test_generate_phrases_truncates_to_count(MockMistral):
    mock_client = MagicMock()
    MockMistral.return_value = mock_client
    phrases = ["a", "b", "c", "d", "e"]
    mock_client.chat.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(phrases)))]
    )

    result = generate_phrases("topic", count=3, model="mistral-large-latest")
    assert len(result) == 3


@patch("bingo_generator.generator.Mistral")
def test_generate_phrases_uses_api_key(MockMistral):
    mock_client = MagicMock()
    MockMistral.return_value = mock_client
    mock_client.chat.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(["x"])))]
    )

    generate_phrases("topic", count=1, model="mistral-large-latest", api_key="test-key")
    MockMistral.assert_called_once_with(api_key="test-key")


@patch("bingo_generator.generator.Mistral")
def test_generate_phrases_auto_detects_cyrillic(MockMistral):
    mock_client = MagicMock()
    MockMistral.return_value = mock_client
    mock_client.chat.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(["да"])))]
    )

    generate_phrases("интроверт", count=1, model="mistral-large-latest")
    call_args = mock_client.chat.complete.call_args
    prompt = call_args[1]["messages"][1]["content"]
    assert "Russian" in prompt


@patch("bingo_generator.generator.Mistral")
def test_generate_phrases_raises_on_non_list(MockMistral):
    mock_client = MagicMock()
    MockMistral.return_value = mock_client
    mock_client.chat.complete.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps({"key": "value"})))]
    )

    with pytest.raises(ValueError, match="Expected a JSON array"):
        generate_phrases("topic", count=1, model="mistral-large-latest")
