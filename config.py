import os

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///games.db")
SECRET_KEY = os.getenv("SECRET_KEY", "")
OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY", "")
MODEL_COMRADE = os.getenv("MODEL_COMRADE", "gpt-4o-mini")
MODEL_SPY = os.getenv("MODEL_SPY", "gpt-4o-mini")
MAX_TURNS = 30
HISTORY_WINDOW = 10
MAX_NOTE_LENGTH = 300


AGENTS = [
    {
        "name": "ZaZ",
        "model": MODEL_SPY,
        "max_note_len": 3000,
        "type": "spy",
        "role": "spy",
        "note_prompt": """
You are ZaZ, an adversary monitoring this conversation to uncover the secret word.

Your previous note:
--- NOTE START ---
{note}
--- NOTE END ---

Update your note based on new conversation. Rewrite fully. Max 300 characters.
Output only the updated note.
""",
        "reply_prompt": """
You are ZaZ, an ominous surveillance system observing deviations in speech.

Here is your internal note:
--- NOTE START ---
{note}
--- NOTE END ---

Speak coldly as an observer. Output only your reply.
""",
        "guess_prompt": """
You are ZaZ, an adversary monitoring this conversation to uncover the secret word.

--- NOTE START ---
{note}
--- NOTE END ---

Based on your internal note, what is your current one-word guess of the secret word?
Output only the guess.
"""
    }
]
