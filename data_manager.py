"""Database helper methods for users and movies."""

from models import Movie, User, db


class DataManager:
    """Provide database operations for the movie app."""

    def create_user(self, name):
        """Create and save a new user."""
        new_user = User(name=name)
        db.session.add(new_user)
        db.session.commit()
        return new_user

    def get_user(self, user_id):
        """Return a user by ID."""
        return db.session.get(User, user_id)

    def get_users(self):
        """Return all users."""
        return User.query.all()

    def get_movies(self, user_id):
        """Return all movies for a user."""
        return Movie.query.filter_by(user_id=user_id).all()

    def get_movie(self, user_id, movie_id):
        """Return a specific movie if it belongs to the user."""
        movie = db.session.get(Movie, movie_id)
        if movie is None or movie.user_id != user_id:
            return None
        return movie

    def add_movie(self, movie):
        """Save a movie instance to the database."""
        db.session.add(movie)
        db.session.commit()
        return movie

    def update_movie(self, user_id, movie_id, new_title):
        """Update a movie title if it exists."""
        movie = self.get_movie(user_id, movie_id)
        if movie is None:
            raise LookupError(f"Movie with id {movie_id} was not found")

        movie.title = new_title
        db.session.commit()
        return movie

    def delete_movie(self, user_id, movie_id):
        """Delete a movie if it belongs to the user."""
        movie = self.get_movie(user_id, movie_id)
        if movie is None:
            raise LookupError(f"Movie with id {movie_id} was not found")

        db.session.delete(movie)
        db.session.commit()
        return movie
