import json
import logging

from mistralai.client import Mistral

logger = logging.getLogger(__name__)


def _detect_lang_hint(topic: str) -> str:
    has_cyrillic = any("Ѐ" <= c <= "ӿ" for c in topic)
    lang = "Russian" if has_cyrillic else "English"
    logger.debug("Detected language hint '%s' for topic '%s'", lang, topic)
    return lang


def generate_phrases(
    topic: str,
    count: int,
    model: str,
    api_key: str = "",
    lang_hint: str = "",
) -> list[str]:
    if not lang_hint or lang_hint == "auto":
        lang_hint = _detect_lang_hint(topic)

    prompt = (
        f"Generate exactly {count} short, funny, relatable bingo phrases about '{topic}'. "
        f"Each phrase should be 2-8 words. "
        f"Write them in {lang_hint}. "
        f'Return ONLY a JSON array of strings, no other text. Example: ["phrase1", "phrase2"]'
    )

    logger.debug(
        "Calling Mistral API: model=%s, topic='%s', count=%d, lang=%s",
        model,
        topic,
        count,
        lang_hint,
    )

    client = Mistral(api_key=api_key) if api_key else Mistral()

    response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a creative assistant that generates humorous "
                    "bingo card content. Always respond with valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
    )

    content = response.choices[0].message.content.strip()
    logger.debug("Mistral raw response: %s", content[:200])

    try:
        phrases = json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Failed to parse Mistral response as JSON: %s", content[:100])
        raise

    if not isinstance(phrases, list):
        logger.warning("Mistral returned non-array type: %s", type(phrases).__name__)
        raise ValueError("Expected a JSON array of strings")

    result = [str(p) for p in phrases[:count]]
    logger.debug("Parsed %d phrases", len(result))
    return result
