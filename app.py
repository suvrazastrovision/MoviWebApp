import json
import os
import secrets
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError
from data_manager import DataManager
from models import db, Movie


load_dotenv(Path(__file__).resolve().parent / ".env")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
database_path = Path(__file__).resolve().parent / "data" / "movies.db"
database_path.parent.mkdir(parents=True, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path.as_posix()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

data_manager = DataManager()


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(SQLAlchemyError)
def handle_database_error(error):
    db.session.rollback()
    app.logger.error(
        "A database operation failed.",
        exc_info=(type(error), error, error.__traceback__),
    )
    return render_template("500.html"), 500


@app.route("/")
def index():
    return render_template("index.html", users=data_manager.get_users())


@app.route("/users", methods=["POST"])
def create_user():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Please enter a user name.", "error")
        return redirect(url_for("index"))

    data_manager.create_user(name)
    flash(f"Added {name}.", "success")
    return redirect(url_for("index"))


@app.route("/users/<int:user_id>/movies", methods=["GET"])
def user_movies(user_id):
    user = data_manager.get_user(user_id)
    if user is None:
        abort(404)

    return render_template(
        "movies.html",
        user=user,
        movies=data_manager.get_movies(user_id),
    )


@app.route("/users/<int:user_id>/movies", methods=["POST"])
def create_movie(user_id):
    user = data_manager.get_user(user_id)
    if user is None:
        abort(404)

    title = request.form.get("title", "").strip()
    if not title:
        flash("Please enter a movie title.", "error")
        return redirect(url_for("user_movies", user_id=user_id))

    api_key = os.environ.get("OMDB_API_KEY")
    if not api_key:
        flash("Movie lookup is unavailable. Set the OMDB_API_KEY environment variable.", "error")
        return redirect(url_for("user_movies", user_id=user_id))

    query = urlencode({"apikey": api_key, "t": title})
    try:
        with urlopen(f"https://www.omdbapi.com/?{query}", timeout=10) as response:
            movie_data = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        app.logger.warning(
            "OMDb lookup failed for submitted movie title (%s).",
            type(error).__name__,
        )
        flash("Could not retrieve movie information from OMDb. Please try again.", "error")
        return redirect(url_for("user_movies", user_id=user_id))

    if not isinstance(movie_data, dict):
        flash("OMDb returned an invalid response. Please try again.", "error")
        return redirect(url_for("user_movies", user_id=user_id))

    if movie_data.get("Response") != "True":
        error_message = movie_data.get("Error")
        flash(
            error_message if isinstance(error_message, str) else "OMDb did not return movie information.",
            "error",
        )
        return redirect(url_for("user_movies", user_id=user_id))

    def omdb_value(field):
        value = movie_data.get(field)
        return value if isinstance(value, str) and value != "N/A" else None

    movie = Movie(
        title=omdb_value("Title") or title,
        director=omdb_value("Director"),
        year=omdb_value("Year"),
        rating=omdb_value("imdbRating"),
        poster=omdb_value("Poster"),
        user_id=user_id,
    )
    data_manager.add_movie(movie)
    flash(f"Added {movie.title} to {user.name}'s favorites.", "success")
    return redirect(url_for("user_movies", user_id=user_id))


@app.route(
    "/users/<int:user_id>/movies/<int:movie_id>/update",
    methods=["POST"],
)
def update_movie(user_id, movie_id):
    if data_manager.get_user(user_id) is None:
        abort(404)

    new_title = request.form.get("title", "").strip()
    if not new_title:
        flash("Please enter a movie title.", "error")
        return redirect(url_for("user_movies", user_id=user_id))

    try:
        data_manager.update_movie(user_id, movie_id, new_title)
    except LookupError:
        abort(404)

    flash("Movie title updated.", "success")
    return redirect(url_for("user_movies", user_id=user_id))


@app.route(
    "/users/<int:user_id>/movies/<int:movie_id>/delete",
    methods=["POST"],
)
def delete_movie(user_id, movie_id):
    if data_manager.get_user(user_id) is None:
        abort(404)

    try:
        data_manager.delete_movie(user_id, movie_id)
    except LookupError:
        abort(404)

    flash("Movie removed from favorites.", "success")
    return redirect(url_for("user_movies", user_id=user_id))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run()
