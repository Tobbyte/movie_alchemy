"""Movie Alchemy app."""
import os
from typing import Any

from config import (
    API_ERR_404_NOT_FOUND,
    API_ERR_INTERNAL_SERVER_ERROR,
    API_ERR_METHOD_NOT_ALLOWED,
    API_ERR_TOO_MANY_REQUESTS,
)
from datamanager import DataManager
from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from setup_db import DB
from werkzeug import Response
from werkzeug.exceptions import HTTPException

from movie_alchemy.models import Movie, User, UsersFavorite

basedir = os.path.abspath(os.path.dirname(__file__))


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

        # self.app.add_url_rule(
        #     "/api/posts",
        #     view_func=self.get_posts_api,
        #     methods=["GET", "POST"],
        # )

        # self.app.add_url_rule(
        #     "/api/posts/<int:post_id>",
        #     view_func=self.delete_post_api,
        #     methods=["DELETE"],
        # )

        # self.app.add_url_rule(
        #     "/api/posts/<int:post_id>",
        #     view_func=self.update_post_api,
        #     methods=["PUT"],  # should be PATCH, but exercise says PUT
        # )

        # self.app.add_url_rule(
        #     "/api/posts/<int:post_id>/like",
        #     view_func=self.like_post_api,
        #     methods=["POST"],
        # )

        # self.app.add_url_rule(
        #     "/api/posts/search",
        #     view_func=self.search_posts_api,
        #     methods=["GET"],
        # )

    ### route handlers ###

    def index(self) -> str:
        """Return a simple message for the root route."""
        return "Welcome to MoviWeb App!"

    def run(self, **kwargs: Any) -> None:
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
