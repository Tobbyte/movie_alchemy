"""Movie Alchemy app."""
import os
from typing import Any

import requests
from config import (
    API_ERR_404_NOT_FOUND,
    API_ERR_INTERNAL_SERVER_ERROR,
    API_ERR_INVALID_REQUEST_DATA,
    API_ERR_METHOD_NOT_ALLOWED,
    API_ERR_TOO_MANY_REQUESTS,
)
from datamanager import DataManager
from flask import Flask, jsonify, redirect, request, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from setup_db import DB
from werkzeug import Response
from werkzeug.exceptions import HTTPException

from movie_alchemy.models import Movie, User, UsersFavorite

DB_USER_NAME = "name"

class InvalidParamError(Exception):
    """A query parameter is unknown or has an invalid value."""


class MovieAlchemyApp:
    """Main application class for Movie Alchemy."""

    def __init__(self) -> None:
        """Initialize the MovieAlchemyApp."""
        self.app = Flask(__name__)
        self.data_manager = DataManager()
        self.db = (
            self.data_manager.db
        )  # Access the DB instance from DataManager
        Limiter(
            key_func=get_remote_address,
            app=self.app,
            default_limits=["100 per minute"],
        )

        # init_swagger_ui(self.app)  # noqa: ERA001

        self.setup_routes()
        self.setup_error_handlers()

    def setup_error_handlers(self) -> None:
        """Register JSON error handlers for the API application."""
        self.app.register_error_handler(404, self.api_page_not_found)
        self.app.register_error_handler(405, self.api_method_not_allowed)
        self.app.register_error_handler(429, self.api_too_many_requests)
        self.app.register_error_handler(500, self.api_internal_server_error)
        self.app.register_error_handler(
            InvalidParamError,
            self.api_invalid_params,
        )

    @staticmethod
    def api_page_not_found(_: HTTPException) -> tuple[Response, int]:
        """Return a JSON response for 404."""
        return jsonify({"error": API_ERR_404_NOT_FOUND}), 404

    @staticmethod
    def api_method_not_allowed(_: HTTPException) -> tuple[Response, int]:
        """Return a JSON response for method forbidden."""
        return jsonify({"error": API_ERR_METHOD_NOT_ALLOWED}), 405

    @staticmethod
    def api_too_many_requests(_: HTTPException) -> tuple[Response, int]:
        """Return JSON for when rate limit is exceeded."""
        return jsonify({"error": API_ERR_TOO_MANY_REQUESTS}), 429

    @staticmethod
    def api_internal_server_error(_: Exception) -> tuple[Response, int]:
        """Return a JSON response for internal API errors."""
        return jsonify({"error": API_ERR_INTERNAL_SERVER_ERROR}), 500

    @staticmethod
    def api_invalid_params(error: InvalidParamError) -> tuple[Response, int]:
        """Return a JSON 400 naming the invalid parameter."""
        return jsonify({"error": str(error)}), 400

    @staticmethod
    def api_db_error(error: Exception) -> tuple[Response, int]:
        """Return a JSON 500 for database errors."""
        return jsonify({"error": "Database error", "details": str(error)}), 500

    def setup_routes(self) -> None:
        """Set up the API routes for the Flask app."""
        self.app.add_url_rule(
            "/",
            view_func=self.index,
            methods=["GET"],
        )

        self.app.add_url_rule(
            "/users",
            view_func=self.list_users,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/users/<int:user_id>/movies<",
            view_func=self.users_movies,
            methods=["GET", "Post"],
        )

        self.app.add_url_rule(
            "/users/<int:user_id>/movies/<int:movie_id>/update",
            view_func=self.update_movie_details,
            methods=["Post"],
        )

    ### route handlers ###

    def index(self) -> str:
        """Return a simple message for the root route."""
        return "Welcome to MoviWeb App!"

    def list_users(self) -> Response | tuple[Response, int]:
        """List all users or create a new user."""
        if request.method == "POST":
            return self.create_user()

        users = self.data_manager.get_users()
        return jsonify([user.as_dict() for user in users]), 200

    def users_movies(self, user_id: int) -> tuple[Response, int]:
        """List all movies."""
        if request.method == "POST":
            return self.add_movie()
        user = self.data_manager.get_user_by_id(user_id)
        if not user:
            return jsonify({"error": API_ERR_404_NOT_FOUND}), 404

        favorites = [
            fav.movie_id
            for fav in self.data_manager.db
            .session_factory()
            .query(
                UsersFavorite,
            )
            .filter_by(user_id=user_id)
        ]
        return jsonify(favorites), 200

    def create_user(self) -> Response:
        """Create a new user."""
        new_user_data_raw = request.get_json(silent=True)

        if (
            not new_user_data_raw  # pylint: disable=too-many-boolean-expressions
            or not isinstance(new_user_data_raw, dict)
            or not all(
                isinstance(cont, str) for cont in new_user_data_raw.values()
            )
            or not new_user_data_raw.get(DB_USER_NAME, "").strip()
        ):
            # return jsonify({"error": API_ERR_INVALID_REQUEST_DATA}), 400
            return redirect(url_for("index"), 404)  # TODO

        new_user = self.data_manager.create_user(
            new_user_data_raw[DB_USER_NAME],
        )

        # return jsonify(new_user), 201
        return redirect(url_for("index"))

    def add_movie(self) -> tuple[Response, int]:
        """Add a new movie."""
        new_movie_data_raw = request.get_json(silent=True)

        if (
            not new_movie_data_raw  # pylint: disable=too-many-boolean-expressions
            or not isinstance(new_movie_data_raw, dict)
            or not all(
                isinstance(cont, str) for cont in new_movie_data_raw.values()
            )
            or not new_movie_data_raw.get("name", "").strip()
        ):
            return jsonify({"error": API_ERR_INVALID_REQUEST_DATA}), 400

        omdb_movie = self.fetch_omdb_data(new_movie_data_raw["name"])
        if omdb_movie:
            first_result = omdb_movie[0]
            new_movie_data_raw.update({
                "name": first_result.get("title", new_movie_data_raw["name"]),
                "year": int(first_result.get("Year")),
                "director": first_result.get("Director"),
                "poster_url": first_result.get("Poster"),
                "imdb_id": first_result.get("imdbID"),
            })

        self.data_manager.add_movie(
            name=new_movie_data_raw["name"],
        )

        return jsonify({"message": "Movie added successfully"}), 201

    def update_movie_details(
        self,
        user_id: int,
        movie_id: int,
    ) -> tuple[Response, int]:
        """Update movie details for a user's favorite movie."""
        data = request.get_json(silent=True)

        if (
            not data
            or not isinstance(data, dict)
            or "movie_id" not in data
            or "user_id" not in data
            or "new_title" not in data
        ):
            return jsonify({"error": API_ERR_INVALID_REQUEST_DATA}), 400

        # Check if the user and movie exist
        user = self.data_manager.get_user_by_id(user_id)
        movie = self.data_manager.get_movie_by_id(movie_id)

        if not user or not movie:
            return jsonify({"error": API_ERR_404_NOT_FOUND}), 404

        # Update the movie details
        movie.name = data["new_title"]

        self.data_manager.save_object(movie)

        return jsonify({"message": "Movie details updated successfully"}), 200

    def fetch_omdb_data(self, movie_name: str) -> dict | None:
        """Fetch movie data from the OMDb API."""
        api_key = os.getenv("OMDB_API_KEY")
        if not api_key:
            raise ValueError("OMDB_API_KEY environment variable is not set.")

        url = f"http://www.omdbapi.com/?t={movie_name}&apikey={api_key}"
        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get("Response") == "True":
                return {
                    "title": data.get("Title"),
                    "year": data.get("Year"),
                    "director": data.get("Director"),
                    "poster_url": data.get("Poster"),
                    "imdb_id": data.get("imdbID"),
                }
        return None

    def run(self, **kwargs: Any) -> None:  # noqa: ANN401
        """Start the Flask app."""
        self.app.run(**kwargs)


def populate_sample_data(data_manager: DataManager) -> None:
    """Populate the database with sample data."""
    # Create sample users
    user1 = data_manager.create_user("Alice")
    user2 = data_manager.create_user("Bob")

    # Create sample movies
    movie1 = Movie(
        name="Inception",
        director="Christopher Nolan",
        year=2010,
        poster_url="https://example.com/inception.jpg",
        imdb_id="tt1375666",
    )
    movie2 = Movie(
        name="The Matrix",
        director="The Wachowskis",
        year=1999,
        poster_url="https://example.com/matrix.jpg",
        imdb_id="tt0133093",
    )

    # Save movies to the database
    data_manager.save_object(movie1)
    data_manager.save_object(movie2)

    print(movie2)

    # Create sample favorites
    favorite1 = UsersFavorite(user_id=user1.id, movie_id=movie1.id)
    favorite2 = UsersFavorite(user_id=user2.id, movie_id=movie2.id)

    # Save favorites to the database
    data_manager.save_object(favorite1)
    data_manager.save_object(favorite2)


if __name__ == "__main__":
    db = DB()
    db.reset_db()
    db.create_tables()
    populate_sample_data(DataManager())
    MovieAlchemyApp().run(debug=True, port=5000)
