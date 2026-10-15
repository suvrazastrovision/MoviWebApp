from models import db, User, Movie


class DataManager:
    def create_user(self, name):
        new_user = User(name=name)
        db.session.add(new_user)
        db.session.commit()
        return new_user

    def get_users(self):
        return User.query.all()

    def get_movies(self, user_id):
        return Movie.query.filter_by(user_id=user_id).all()

    def add_movie(self, movie):
        db.session.add(movie)
        db.session.commit()
        return movie

    def update_movie(self, movie_id, new_title):
        movie = db.session.get(Movie, movie_id)
        if movie is None:
            raise LookupError(f"Movie with id {movie_id} was not found")

        movie.title = new_title
        db.session.commit()
        return movie

    def delete_movie(self, movie_id):
        movie = db.session.get(Movie, movie_id)
        if movie is None:
            raise LookupError(f"Movie with id {movie_id} was not found")

        db.session.delete(movie)
        db.session.commit()
        return movie
