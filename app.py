from pathlib import Path

from flask import Flask
from data_manager import DataManager
from models import db


app = Flask(__name__)
database_path = Path(__file__).resolve().parent / "data" / "movies.db"
database_path.parent.mkdir(parents=True, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path.as_posix()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

data_manager = DataManager()


@app.route("/")
def home():
    return "Welcome to MoviWeb App!"


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run()
