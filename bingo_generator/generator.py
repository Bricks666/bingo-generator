import json
import logging
import re

from mistralai.client import Mistral

logger = logging.getLogger(__name__)

OVERREQUEST_MARGIN = 10

SYSTEM_PROMPT = """\
You are a comedy writer creating viral bingo cards.

Your job: given a topic, a count, and a language — generate that many \
bingo cell phrases. Each phrase must be a short, funny, absurdly specific \
observation that people who relate to the topic would instantly recognize.

STYLE RULES:
- Hyper-specific, not generic. "Rehearsed a phone call for 10 minutes" \
is good. "Doesn't like calling" is boring.
- Include absurd exaggerations, irrational behaviors, embarrassing habits.
- Mix types: thoughts, actions, physical reactions, rationalizations, excuses.

DIVERSITY RULES:
- Each cell must cover a DIFFERENT aspect. Spread across these categories:
  * Social interactions (parties, dates, meetings, strangers)
  * Inner monologue (doubts, overthinking, self-talk)
  * Physical reactions (sweating, freezing, heart racing)
  * Daily routines (morning, commute, bedtime, weekends)
  * Avoidance strategies (excuses, escape plans, hiding)
  * Relationships (friends, family, romance, coworkers)
  * Digital life (messaging, social media, doomscrolling)
  * Irrational fears and embarrassing habits
- Never express the same idea twice, even with different words.
  If one cell says "avoids eye contact", no other cell about eye contact.
- If two cells could describe the same moment, they are too similar.

FORMAT:
- 2-8 words each.
- Return ONLY a JSON array of strings. No markdown, no code blocks, no explanation.
- Example: ["phrase one", "phrase two", "phrase three"]\
"""


def _detect_lang_hint(topic: str) -> str:
    has_cyrillic = any("Ѐ" <= c <= "ӿ" for c in topic)
    lang = "Russian" if has_cyrillic else "English"
    logger.debug("Detected language hint '%s' for topic '%s'", lang, topic)
    return lang


def _tokenize(text: str) -> set[str]:
    return {w for w in re.sub(r"[^\w\s]", "", text.lower()).split() if len(w) > 3}


def _is_near_duplicate(phrase: str, existing: list[str]) -> bool:
    bag = _tokenize(phrase)
    if len(bag) < 2:
        return False
    for other in existing:
        other_bag = _tokenize(other)
        if not other_bag:
            continue
        shared = bag & other_bag
        ratio = len(shared) / max(len(bag), len(other_bag))
        if ratio > 0.7:
            return True
    return False


def generate_phrases(
    topic: str,
    count: int,
    model: str,
    api_key: str = "",
    lang_hint: str = "",
) -> list[str]:
    if not lang_hint or lang_hint == "auto":
        lang_hint = _detect_lang_hint(topic)

    request_count = count + OVERREQUEST_MARGIN

    user_message = f"Topic: {topic}\nCount: {request_count}\nLanguage: {lang_hint}"

    logger.debug(
        "Calling Mistral API: model=%s, topic='%s', request=%d, need=%d, lang=%s",
        model,
        topic,
        request_count,
        count,
        lang_hint,
    )

    client = Mistral(api_key=api_key) if api_key else Mistral()

    response = client.chat.complete(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=1.0,
    )

    content = response.choices[0].message.content.strip()
    logger.debug("Mistral raw response (first 300 chars): %s", content[:300])

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

    phrases = [str(p) for p in phrases]
    logger.debug("Mistral returned %d phrases", len(phrases))

    # Dedup: exact first, then near-duplicate
    result: list[str] = []
    for phrase in phrases:
        if phrase not in result and not _is_near_duplicate(phrase, result):
            result.append(phrase)

    removed = len(phrases) - len(result)
    if removed:
        logger.warning(
            "Removed %d duplicates (%d exact, %d near) from %d phrases",
            removed,
            len(phrases) - len(set(phrases)),
            removed - (len(phrases) - len(set(phrases))),
        )

    result = result[:count]
    logger.debug("Final: %d phrases (requested %d)", len(result), count)
    return result
