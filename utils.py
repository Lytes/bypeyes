import re
import requests
import datetime as dt

GUESS_RE = re.compile(r"\[\[guess:\s*([a-zA-Z]{2,})\s*]]", re.I)


def is_valid_word(word: str) -> bool:
    if not hasattr(is_valid_word, "_cache"):
        is_valid_word._cache = {}
    cache = is_valid_word._cache
    word = word.lower()
    now = dt.datetime.utcnow().timestamp()
    if (cached := cache.get(word)) and now - cached[1] < 60:
        return cached[0]

    try:
        r = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=4
        )
        ok = r.status_code == 200
    except requests.RequestException:
        ok = False
    cache[word] = (ok, now)
    return ok
