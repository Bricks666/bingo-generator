import json
from mistralai.client import Mistral


def _detect_lang_hint(topic: str) -> str:
    has_cyrillic = any("Ѐ" <= c <= "ӿ" for c in topic)
    if has_cyrillic:
        return "Russian"
    return "English"


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
        f"Return ONLY a JSON array of strings, no other text. Example: [\"phrase1\", \"phrase2\"]"
    )

    client = Mistral(api_key=api_key) if api_key else Mistral()

    response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a creative assistant that generates humorous bingo card content. Always respond with valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
    )

    content = response.choices[0].message.content.strip()
    phrases = json.loads(content)

    if not isinstance(phrases, list):
        raise ValueError("Expected a JSON array of strings")

    return [str(p) for p in phrases[:count]]
