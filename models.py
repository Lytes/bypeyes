import enum
import datetime as dt
from sqlalchemy.orm import validates
from db import db


class GameStatus(enum.Enum):
    RAMP = "RAMP"
    PLAY = "PLAY"
    PARTIAL = "PARTIAL"
    WIN = "WIN"
    LOSE = "LOSE"


class Game(db.Model):
    id = db.Column(db.String, primary_key=True)
    player1_secret = db.Column(db.String, nullable=False)
    player2_secret = db.Column(db.String, nullable=False, default="")
    status = db.Column(db.Enum(GameStatus), default=GameStatus.RAMP)
    turns = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime, default=dt.datetime.utcnow)
    spy_note = db.Column(db.Text, nullable=False, default="")
    p1_guessed = db.Column(db.Boolean, default=False)
    p2_guessed = db.Column(db.Boolean, default=False)

    @validates("player1_secret", "player2_secret")
    def _lowercase(self, key, value: str):
        return value.lower()

# models.py


class Replay(db.Model):
    """
    One row per turn.  JSON keeps the agent blob flexible
    and avoids a tangle of extra tables for notes / guesses.
    """
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String,
                        db.ForeignKey("game.id"),
                        index=True)
    turn = db.Column(db.Integer, nullable=False)
    ts = db.Column(db.DateTime,
                   default=dt.datetime.utcnow,
                   nullable=False)
    turn_lines = db.Column(db.JSON, nullable=False)
    # "PLAY" / "WIN" / "LOSE"
    outcome = db.Column(db.String, nullable=False)
    # { name: {note,reply,guess}, ... }
    agents = db.Column(db.JSON, nullable=False)


class Msg(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String, db.ForeignKey("game.id"))
    role = db.Column(db.String)
    text = db.Column(db.Text)
    guess = db.Column(db.String, nullable=True)
    ts = db.Column(db.DateTime, default=dt.datetime.utcnow)
    sender = db.Column(db.String)  # 'player1' or 'player2'
    used = db.Column(db.Boolean, default=False)


class AgentState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String, db.ForeignKey("game.id"))
    agent_name = db.Column(db.String, nullable=False)
    agent_type = db.Column(db.String, nullable=False)
    note = db.Column(db.Text, nullable=False, default="")
    updated_at = db.Column(
        db.DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
