import os
import secrets
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from data_manager import DataManager
from models import db, Movie, User


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
database_path = Path(__file__).resolve().parent / "data" / "movies.db"
database_path.parent.mkdir(parents=True, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path.as_posix()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

data_manager = DataManager()


@app.route("/")
def home():
    return render_template("home.html", users=data_manager.get_users())


@app.route("/users", methods=["POST"])
def create_user():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Please enter a user name.", "error")
        return redirect(url_for("home"))

    data_manager.create_user(name)
    flash(f"Added {name}.", "success")
    return redirect(url_for("home"))


@app.route("/users/<int:user_id>/movies", methods=["GET"])
def user_movies(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    return render_template(
        "movies.html",
        user=user,
        movies=data_manager.get_movies(user_id),
    )


@app.route("/users/<int:user_id>/movies", methods=["POST"])
def create_movie(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    title = request.form.get("title", "").strip()
    if not title:
        flash("Please enter a movie title.", "error")
        return redirect(url_for("user_movies", user_id=user_id))

    movie = Movie(
        title=title,
        director=request.form.get("director", "").strip() or None,
        year=request.form.get("year", "").strip() or None,
        rating=request.form.get("rating", "").strip() or None,
        poster=request.form.get("poster", "").strip() or None,
        user_id=user_id,
    )
    data_manager.add_movie(movie)
    flash(f"Added {title} to {user.name}'s favorites.", "success")
    return redirect(url_for("user_movies", user_id=user_id))


@app.route(
    "/users/<int:user_id>/movies/<int:movie_id>/update",
    methods=["POST"],
)
def update_movie(user_id, movie_id):
    movie = Movie.query.filter_by(id=movie_id, user_id=user_id).first_or_404()
    new_title = request.form.get("title", "").strip()
    if not new_title:
        flash("Please enter a movie title.", "error")
        return redirect(url_for("user_movies", user_id=user_id))

    data_manager.update_movie(movie.id, new_title)
    flash("Movie title updated.", "success")
    return redirect(url_for("user_movies", user_id=user_id))


@app.route(
    "/users/<int:user_id>/movies/<int:movie_id>/delete",
    methods=["POST"],
)
def delete_movie(user_id, movie_id):
    movie = Movie.query.filter_by(id=movie_id, user_id=user_id).first_or_404()
    data_manager.delete_movie(movie.id)
    flash("Movie removed from favorites.", "success")
    return redirect(url_for("user_movies", user_id=user_id))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run()
