from config import DB_PATH, SECRET_KEY
from db import db
from models import Game, Msg, GameStatus, Replay
from logic import run_turn
from utils import is_valid_word, GUESS_RE
import secrets
from flask import Flask,  session, abort, Response, render_template, request, redirect, url_for, abort, jsonify
import os
import uuid
from functools import wraps
from flask_wtf.csrf import CSRFProtect
import json

from types import SimpleNamespace

app = Flask(__name__)
app.config.update(SQLALCHEMY_DATABASE_URI=DB_PATH,
                  SQLALCHEMY_TRACK_MODIFICATIONS=False,
                  WTF_CSRF_TIME_LIMIT=None)

app.config["SECRET_KEY"] = SECRET_KEY
CSRFProtect(app)
db.init_app(app)


def require_player_auth(func):
    @wraps(func)
    def wrapper(game_id, *args, **kwargs):
        if 'player_token' not in session or 'player_role' not in session:
            abort(403, "No player session found")
        if session.get('game_id') != game_id:
            abort(403, "Invalid game session")
        return func(game_id, *args, **kwargs)
    return wrapper


with app.app_context():
    db.create_all()


@app.get("/")
def index():
    return render_template("index.html", error=None)


@app.post("/start")
def start():
    player1_secret = request.form.get("secret", "").strip()
    if not is_valid_word(player1_secret):
        return render_template("index.html", error="Not a valid English word.")

    game_id = uuid.uuid4().hex[:]
    game = Game(id=game_id, player1_secret=player1_secret.lower(), spy_note="")
    db.session.add(game)
    db.session.commit()
    session['player_token'] = secrets.token_hex(16)
    session['player_role'] = 'player1'
    session['game_id'] = game_id
    player2_url = url_for('start_player2', game_id=game.id, _external=True)
    return render_template("index.html", game_id=game.id, player2_url=player2_url)


@app.get("/start_player2/<game_id>")
def start_player2(game_id):
    game = Game.query.get_or_404(game_id)

    if not game.player1_secret:  # Ensure Player 1 has entered their word
        return render_template("index.html", error="Player 1 has not yet started the game.")

    if game.player2_secret and game.player2_secret != "":  # Check if Player 2 has already joined
        return render_template("index.html", error="Player 2 has already entered their secret word.")

    return render_template("join_game.html", game_id=game.id)


@app.post("/start_player2/<game_id>")
def join_game(game_id):
    player2_secret = request.form.get("player2_secret", "").strip()
    if not is_valid_word(player2_secret):
        return render_template("join_game.html", error="Secret word must be valid.")

    game = Game.query.get_or_404(game_id)
    game.player2_secret = player2_secret.lower()  # Store Player 2's word
    game.status = GameStatus.PLAY
    db.session.commit()

    session['player_token'] = secrets.token_hex(16)
    session['player_role'] = 'player2'
    session['game_id'] = game_id

    return redirect(url_for("game", game_id=game.id))


@app.get("/poll/<game_id>")
def poll(game_id):
    game = Game.query.get_or_404(game_id)
    after_id = int(request.args.get("after_id", 0))
    new_msgs = Msg.query.filter(
        Msg.game_id == game_id,
        Msg.id > after_id
    ).order_by(Msg.id.asc()).all()
    # correct_by = None
    # guessed_word = None
    # if game.status == GameStatus.PARTIAL:
    #     if game.p1_guessed and not game.p2_guessed:
    #         correct_by = "player1"
    #     elif game.p2_guessed and not game.p1_guessed:
    #         correct_by = "player2"
    response = {
        "messages": [{
            "id":     m.id,
            "role":   m.role,
            "sender": m.sender,
            "text":   m.text,
            # 1-liner: show player guess only when it’s right
            "guess": (
                m.guess if m.role != "Player" else
                m.guess if (
                    (m.sender == "player1" and m.guess == game.player2_secret) or
                    (m.sender == "player2" and m.guess == game.player1_secret)
                ) else ""
            )
        } for m in new_msgs],
        "status": game.status.value,
        "turns":  game.turns,
    }

    # Add secrets only if game is won
    if game.status == GameStatus.WIN:
        response["player1_secret"] = game.player1_secret
        response["player2_secret"] = game.player2_secret

    return jsonify(response)


@app.get("/g/<game_id>")
def game(game_id):
    game = Game.query.get_or_404(game_id)

    # sanitize: strip all guesses
    raw = (Msg.query
              .filter_by(game_id=game_id)
              .order_by(Msg.id.asc())
              .all())

    msgs = [
        SimpleNamespace(
            id=m.id,
            role=m.role,
            sender=getattr(m, "sender", None),
            text=m.text,
            # always blank → template hides it
            guess=m.guess if m.role != "Player" else ""
        )
        for m in raw
    ]

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("chat_list.html", msgs=msgs)

    return render_template("game.html",
                           game=game,
                           msgs=msgs,
                           max_turns=30)


@app.get("/g/<game_id>/replay")
def download_replay(game_id):
    game = Game.query.get_or_404(game_id)
    if game.status not in {GameStatus.WIN, GameStatus.LOSE}:
        abort(403, "Replay is available only after the game ends.")
    rows = (Replay.query
            .filter_by(game_id=game_id)
            .order_by(Replay.turn.asc())
            .all())
    if not rows:
        abort(404, "No replay found.")

    def generate():
        for r in rows:
            yield json.dumps({
                "game_id": r.game_id,
                "timestamp": r.ts.isoformat(),
                "turn": r.turn,
                "turn_lines": r.turn_lines,
                "agents": r.agents,
                "outcome": r.outcome,
            }) + "\n"

    filename = f"game_{game_id}.jsonl"
    return Response(generate(),
                    mimetype="application/json",
                    headers={"Content-Disposition":
                             f"attachment; filename={filename}"})


@app.route("/hasPlayer2Joined/<game_id>")
def has_player2_joined(game_id):
    game = Game.query.get(game_id)
    joined = game and game.player2_secret is not None and game.player2_secret != ""
    return jsonify({"joined": joined})


@app.post("/g/<game_id>/send")
@require_player_auth
def send(game_id):
    game = Game.query.get_or_404(game_id)
    if game.status.value not in ["PLAY", "PARTIAL"]:
        abort(400, "Game already finished")

    text = request.form.get("text", "").strip()[:400]
    guess = request.form.get("guess", "").strip().lower()

    if not text:
        abort(400, "Empty message")

    text = GUESS_RE.sub("", text)
    new_msg = Msg(
        game_id=game.id,
        role="Player",
        sender=session["player_role"],
        text=text,
        guess=guess,
        used=False
    )
    db.session.add(new_msg)
    db.session.commit()
    run_turn(game)
    print(
        f"The role of this player is {session["player_role"]}, they guessed {guess}")
    print(
        f"player one secret is {game.player1_secret}. . . player 2 secret is {game.player2_secret}"
    )
    if session["player_role"] == "player1" and guess == game.player2_secret:
        game.p1_guessed = True
    elif session["player_role"] == "player2" and guess == game.player1_secret:
        game.p2_guessed = True

    if game.p1_guessed and game.p2_guessed:
        game.status = GameStatus.WIN
    elif game.p1_guessed or game.p2_guessed:
        game.status = GameStatus.PARTIAL
    db.session.commit()
    return redirect(url_for("game", game_id=game.id))


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
