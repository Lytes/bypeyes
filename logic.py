import datetime
import json
import os
import logging

from models import Game, Msg, GameStatus, AgentState, Replay
from config import AGENTS, MAX_TURNS, HISTORY_WINDOW, MAX_NOTE_LENGTH
from db import db
from ai import update_agent_note, generate_guess
from sqlalchemy.exc import SQLAlchemyError

from models import Replay

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPLAY_DIR = "./replay_logs"
os.makedirs(REPLAY_DIR, exist_ok=True)


def get_note(game: Game, agent_type: str) -> str:
    logger.debug(f"Fetching note for agent_type={agent_type}")
    if agent_type == "comrade":
        return game.comrade_note
    elif agent_type == "spy":
        return game.spy_note
    else:
        return ""


def get_agent_state(game_id, agent_name):
    logger.debug(
        f"Querying AgentState for game_id={game_id}, agent_name={agent_name}")
    return AgentState.query.filter_by(game_id=game_id, agent_name=agent_name).first()


def create_agent_state(game_id, agent):
    logger.info(
        f"Creating AgentState for game_id={game_id}, agent={agent['name']}")
    state = AgentState(
        game_id=game_id,
        agent_name=agent["name"],
        agent_type=agent["type"],
        note=""
    )
    db.session.add(state)
    return state


def set_note(state, new_note):
    logger.info(f"Updating note for {state.agent_name}")
    state.note = new_note.strip()[:MAX_NOTE_LENGTH]


def save_replay(game: Game,
                turn_lines: list[dict],
                agent_replies: dict,
                agent_guesses: dict) -> None:
    # build the same dict you already had
    agents_blob = {}
    for agent in AGENTS:
        name = agent["name"]
        state = AgentState.query.filter_by(game_id=game.id,
                                           agent_name=name).first()
        agents_blob[name] = {
            "note": state.note,
            "reply": agent_replies.get(name),
            "guess": agent_guesses.get(name),
        }

    db.session.add(
        Replay(
            game_id=game.id,
            turn=game.turns,
            turn_lines=turn_lines,
            outcome=game.status.value,
            agents=agents_blob,
        )
    )
    db.session.commit()
# --- Full turn engine ---


def run_turn(game: Game) -> None:
    logger.info(f"[run_turn] Checking game_id={game.id}, turn={game.turns}")
    try:
        db.session.begin_nested()

        if game.status not in {GameStatus.PLAY, GameStatus.PARTIAL}:
            logger.warning(f"[run_turn] Game not in PLAY: {game.status}")
            return

        if game.turns >= MAX_TURNS:
            logger.info(f"[run_turn] Max turns hit, marking LOSE")
            game.status = GameStatus.LOSE
            db.session.commit()
            return

        p1_msgs = Msg.query.filter_by(
            game_id=game.id, sender='player1', role='Player', used=False
        ).order_by(Msg.id.asc()).all()

        p2_msgs = Msg.query.filter_by(
            game_id=game.id, sender='player2', role='Player', used=False
        ).order_by(Msg.id.asc()).all()

        if not p1_msgs or not p2_msgs:
            logger.info(
                f"[run_turn] Incomplete: P1={len(p1_msgs)}, P2={len(p2_msgs)}")
            db.session.rollback()
            return  # Wait for both
        print(f"P1 {p1_msgs}\nP2 {p2_msgs}")
        # Mark all as used
        for m in p1_msgs + p2_msgs:
            m.used = True

        logger.info(
            f"[run_turn] Consuming P1: {len(p1_msgs)} P2: {len(p2_msgs)}")

        # Combine for this turn's context
        turn_lines = [
            {"sender": "player1", "text": m.text} for m in p1_msgs
        ] + [
            {"sender": "player2", "text": m.text} for m in p2_msgs
        ]

        msgs = Msg.query.filter_by(game_id=game.id).order_by(
            Msg.id.desc()).limit(HISTORY_WINDOW).all()
        msgs.reverse()

        recent_history = (
            [{"role": "user", "content": f"Player1: {m.text}"} for m in p1_msgs] +
            [{"role": "user", "content": f"Player2: {m.text}"}
                for m in p2_msgs]
        )

        agent_replies = {}
        agent_guesses = {}

        for agent in AGENTS:
            name = agent["name"]
            model = agent["model"]
            logger.info(f"[run_turn] Processing agent: {name}")

            # Load or create state
            state = get_agent_state(game.id, name)
            if not state:
                logger.info(f"No state found for {name}. Creating new state.")
                state = create_agent_state(game.id, agent)
                db.session.flush()

            # Update note
            note_prompt = agent["note_prompt"].format(note=state.note)
            updated_note = update_agent_note(
                model, note_prompt, recent_history)
            logger.info(
                f"Updated note for {name}: {updated_note.strip()[:MAX_NOTE_LENGTH]}")
            set_note(state, updated_note)
            db.session.flush()

            # # Generate reply
            # reply_prompt = agent["reply_prompt"].format(note=state.note)
            # reply = generate_agent_reply(model, reply_prompt, recent_history)
            # logger.info(f"Generated reply for {name}: {reply}")
            # db.session.add(Msg(game_id=game.id, role=name, text=reply))
            # db.session.flush()
            # agent_replies[name] = reply

            # Generate guess
            guess_prompt = agent["guess_prompt"].format(note=state.note)
            guess = generate_guess(model, guess_prompt)
            logger.info(f"Generated guess for {name}: {guess}")
            db.session.add(Msg(game_id=game.id, role=name, text=updated_note.strip()[
                           :MAX_NOTE_LENGTH], guess=guess))
            db.session.flush()
            agent_guesses[name] = guess

        # Evaluate guesses
        for agent in AGENTS:
            guess = agent_guesses.get(agent["name"])
            logger.info(f"Evaluating guess for {agent['name']}: {guess}")
            if guess == game.player1_secret or guess == game.player2_secret:
                if agent["type"] == "spy":
                    logger.info(
                        f"ZaZ guessed the secret {guess}! Marking game {game.id} as LOSE.")
                    game.status = GameStatus.LOSE
                    break
                # elif agent["type"] == "comrade":
                #     logger.info(f"Comrade guessed the secret! Marking game {game.id} as WIN.")
                #     game.status = GameStatus.WIN
                #     break

        game.turns += 1
        logger.info(f"Incremented turns. New turn count: {game.turns}")
        db.session.flush()
        db.session.commit()

        save_replay(game, turn_lines, agent_replies, agent_guesses)

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        db.session.rollback()
        raise RuntimeError(f"DB failure in run_turn: {str(e)}")
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        db.session.rollback()
        raise RuntimeError(f"Critical error in run_turn: {str(e)}")
