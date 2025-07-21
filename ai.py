import re
import openai
from config import OPENAI_API_KEY
import time
import random

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    print("⚠️  OPENAI_API_KEY not set – using offline dummy responses.")


# def _ai_chat(model: str, system_prompt: str, history: list[dict[str, str]]) -> str:
#     print(system_prompt)
#     print(history)
#    #  exit()
#     if not OPENAI_API_KEY:
#         exit(21)
#     rsp = openai.chat.completions.create(
#         model=model,
#         messages=[{"role": "system", "content": system_prompt}] + history,
#         max_tokens=150,
#         temperature=0.7,
#     )
#     return rsp.choices[0].message.content


def update_agent_note(model: str, system_prompt: str, history: list[dict[str, str]]) -> str:
    rsp = openai.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}] + history,
        max_tokens=150,
        temperature=0.7,
    )
    return rsp.choices[0].message.content.strip()


def generate_agent_reply(model: str, reply_prompt: str, history: list[dict[str, str]]) -> str:
    if not OPENAI_API_KEY:
        exit(21)

    rsp = openai.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": reply_prompt}] + history,
        max_tokens=150,
        temperature=0.7,
    )
    return rsp.choices[0].message.content.strip()


# def generate_guess(model: str, guessing_prompt: str) -> str:
#     if not OPENAI_API_KEY:
#         exit(21)

#     rsp = openai.chat.completions.create(
#         model=model,
#         messages=[
#             {"role": "system", "content": "Output only your single word guess."},
#             {"role": "user", "content": guessing_prompt}
#         ],
#         max_tokens=5,
#         temperature=0.5,
#     )
#     return rsp.choices[0].message.content.strip().lower()


def generate_guess(model: str, guessing_prompt: str, attempts: int = 5) -> str:
    """
    Perform soft beam search by sampling multiple guesses and selecting most common.
    """
    if not OPENAI_API_KEY:
        exit(21)

    rsp = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Output only your single word guess."},
            {"role": "user", "content": guessing_prompt}
        ],
        max_tokens=5,
        temperature=0.5,  # lower temp = more consistent guesses
    )
    guess = rsp.choices[0].message.content.strip().lower()
    return guess
