import json
import logging
import re

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
        f"Create a bingo card for the topic '{topic}'.\n"
        f"Generate exactly {count} cells.\n\n"
        f"Each cell must be a short, funny, absurdly specific observation "
        f"that people who relate to '{topic}' would recognize instantly.\n\n"
        f"Rules:\n"
        f"- Be hyper-specific, not generic. 'Pretended to check phone to avoid small talk' "
        f"is good. 'Doesn't like talking' is boring.\n"
        f"- Include absurd exaggerations, irrational behaviors, embarrassing habits.\n"
        f"- Mix types: thoughts ('wait, was that rude?'), actions ('left party without "
        f"saying goodbye'), physical reactions ('heart rate spikes when phone rings'), "
        f"rationalizations ('it's not hoarding, it's a collection').\n"
        f"- Every phrase must be unique, no duplicates or near-duplicates.\n"
        f"- 2-8 words each.\n"
        f"- Write in {lang_hint}.\n\n"
        f'Return ONLY a JSON array of strings. Example: ["phrase1", "phrase2"]'
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
                    "You are a witty comedy writer who specializes in observational humor. "
                    "You write bingo cards that make people laugh and say 'that's literally me'. "
                    "Your phrases are never generic — they are uncomfortably specific, "
                    "absurdly relatable, and sometimes painfully accurate. "
                    "Always respond with valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=1.0,
    )

    content = response.choices[0].message.content.strip()
    logger.debug("Mistral raw response: %s", content[:200])

    # Strip markdown code blocks if present
    content = re.sub(r"^```(?:json)?\s*\n?", "", content)
    content = re.sub(r"\n?```\s*$", "", content)
    content = content.strip()

    try:
        phrases = json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Failed to parse Mistral response as JSON: %s", content[:100])
        raise

    if not isinstance(phrases, list):
        logger.warning("Mistral returned non-array type: %s", type(phrases).__name__)
        raise ValueError("Expected a JSON array of strings")

    result = []
    seen = set()
    for p in phrases:
        text = str(p)
        if text not in seen:
            seen.add(text)
            result.append(text)

    dupes = len(phrases) - len(result)
    if dupes:
        logger.warning("Removed %d duplicate phrases from Mistral response", dupes)

    result = result[:count]
    logger.debug("Parsed %d unique phrases", len(result))
    return result
