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
    LIMITER_DEFAULT_LIMIT,
    OMBD_ERR_MSG,
    OMBD_KEY_NOT_SET_ERROR,
    OMBD_URL,
    STATUS_200_OK,
)
from datamanager import DataManager
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import Movie, UsersFavorite
from setup_db import DB
from sqlalchemy.exc import SQLAlchemyError
from werkzeug import Response
from werkzeug.exceptions import HTTPException


class InvalidParamError(Exception):
    """A query parameter is unknown or has an invalid value."""


load_dotenv()


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
            default_limits=[LIMITER_DEFAULT_LIMIT],
        )

        # init_swagger_ui(self.app)  # noqa: ERA001

        self.setup_routes()
        self.setup_error_handlers()

        self.api_key = os.getenv("OMDB_API_KEY")
        if not self.api_key:
            err_msg = OMBD_KEY_NOT_SET_ERROR
            raise ValueError(err_msg)

    def setup_error_handlers(self) -> None:
        """Register HTML error handlers for the web application."""
        self.app.register_error_handler(404, self.api_page_not_found)
        self.app.register_error_handler(405, self.api_method_not_allowed)
        self.app.register_error_handler(429, self.api_too_many_requests)
        self.app.register_error_handler(500, self.api_internal_server_error)
        self.app.register_error_handler(SQLAlchemyError, self.api_db_error)
        self.app.register_error_handler(RuntimeError, self.api_db_error)
        self.app.register_error_handler(
            InvalidParamError,
            self.api_invalid_params,
        )

    @staticmethod
    def api_page_not_found(_: HTTPException) -> tuple[str, int]:
        """Return a JSON response for 404."""
        return render_template("404.html"), 404

    @staticmethod
    def api_method_not_allowed(_: HTTPException) -> tuple[str, int]:
        """Render the method-not-allowed page."""
        return (
            render_template("404.html", error=API_ERR_METHOD_NOT_ALLOWED),
            405,
        )

    @staticmethod
    def api_too_many_requests(_: HTTPException) -> tuple[str, int]:
        """Render the rate-limit error page."""
        return (
            render_template("500.html", error=API_ERR_TOO_MANY_REQUESTS),
            429,
        )

    @staticmethod
    def api_internal_server_error(_: Exception) -> tuple[str, int]:
        """Render the internal server error page."""
        return (
            render_template("500.html", error=API_ERR_INTERNAL_SERVER_ERROR),
            500,
        )

    @staticmethod
    def api_invalid_params(error: InvalidParamError) -> tuple[str, int]:
        """Render a 400 page naming the invalid parameter."""
        return render_template("500.html", error=str(error)), 400

    @staticmethod
    def api_db_error(_: Exception) -> tuple[str, int]:
        """Render the database error page."""
        return (
            render_template("500.html", error=API_ERR_INTERNAL_SERVER_ERROR),
            500,
        )

    def setup_routes(self) -> None:
        """Set up the API routes for the Flask app."""
        self.app.add_url_rule(
            "/",
            view_func=self.index,
            methods=["GET"],
        )

        self.app.add_url_rule(
            # lists all users or creates a new user
            "/users",
            view_func=self.users,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            # lists all movies for a user or adds a new movie one
            "/users/<int:user_id>/movies",
            view_func=self.users_movies,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            # saves a new movie to a user's favorites
            "/users/<int:user_id>/movies_save",
            view_func=self.users_movies_save,
            methods=["POST"],
        )

        self.app.add_url_rule(
            "/users/<int:user_id>/movies/<int:movie_id>/update",
            view_func=self.update_movie_details,
            methods=["POST"],
        )

        self.app.add_url_rule(
            "/users/<int:user_id>/movies/<int:movie_id>/delete",
            view_func=self.delete_favorite_movie,
            methods=["POST"],
        )

    ### route handlers ###

    def index(self, error: str | None = None) -> str | tuple[str, int]:
        """Render the index page with a list of users.

        for /
        """
        try:
            users = self.data_manager.get_users()
        except RuntimeError:
            return (
                render_template(
                    "500.html",
                    error=API_ERR_INTERNAL_SERVER_ERROR,
                ),
                500,
            )
        error = error or request.args.get("error")
        return render_template("index.html", users=users, error=error)

    def users(self) -> str | Response | tuple[str, int]:
        """List all users or create a new user.

        for /users
        """
        if request.method == "POST":
            return self.create_user()

        users = self.data_manager.get_users()
        return render_template("index.html", users=users)

    def users_movies(self, user_id: int) -> str | Response | tuple[str, int]:
        """List all movies for a user or add a new one.

        for /users/<user_id>/movies
        """
        if request.method == "POST":
            return self.users_movies_add(user_id)

        return self.render_movies_page(
            user_id,
            error=request.args.get("error"),
        )

    def render_movies_page(
        self,
        user_id: int,
        movie_suggestions: dict | None = None,
        search_query: str | None = None,
        error: str | None = None,
    ) -> str | tuple[str, int]:
        """Render a user's movies and optional OMDb suggestions."""
        user = self.data_manager.get_user_by_id(user_id)
        if not user:
            return (
                render_template("404.html", error=API_ERR_404_NOT_FOUND),
                404,
            )

        favorites = self.data_manager.get_favorite_movies(user_id)
        return render_template(
            "movies.html",
            user_name=user.name,
            user_id=user_id,
            movies=favorites,
            movie_suggestions=movie_suggestions,
            search_query=search_query,
            error=error,
        )

    def create_user(self) -> Response | tuple[str, int]:
        """Create a new user."""
        name = request.form.get("name", "").strip()

        if not name:
            return redirect(
                url_for("index", error=API_ERR_INVALID_REQUEST_DATA),
                303,
            )

        self.data_manager.create_user(name)
        return redirect(url_for("index"), 303)

    def users_movies_add(
        self,
        user_id: int,
    ) -> str | Response | tuple[str, int]:
        """Add a new movie."""
        movie_name = request.form.get("movie_name", "").strip()

        if not movie_name:
            return redirect(
                url_for(
                    "users_movies",
                    user_id=user_id,
                    error=API_ERR_INVALID_REQUEST_DATA,
                ),
                303,
            )

        results = self.search_ombd_by_title(movie_name)

        if isinstance(results, dict) and results.get("error"):
            return self.render_movies_page(
                user_id,
                search_query=movie_name,
                error=results["error"],
            )

        return self.render_movies_page(
            user_id,
            results,
            search_query=movie_name,
        )

    def users_movies_save(
        self,
        user_id: int,
    ) -> Response | tuple[str, int]:
        """Save a movie to a user's favorites."""
        movie_name = request.form.get("movie_name", "").strip()

        if not movie_name:
            return redirect(
                url_for(
                    "users_movies",
                    user_id=user_id,
                    error=API_ERR_INVALID_REQUEST_DATA,
                ),
            )

        omdb_movie = self.fetch_omdb_data(movie_name)

        if omdb_movie:
            if omdb_movie.get("error"):
                return redirect(
                    url_for(
                        "users_movies",
                        user_id=user_id,
                        error=omdb_movie.get("error"),
                    ),
                )
            new_movie = self.data_manager.add_movie(
                name=omdb_movie.get("title"),  # pyright: ignore[reportArgumentType]
                year=omdb_movie.get("year"),
                director=omdb_movie.get("director"),
                poster_url=omdb_movie.get("poster_url"),
                imdb_id=omdb_movie.get("imdb_id"),
            )
            self.data_manager.add_favorite(
                user_id=user_id,
                movie_id=new_movie.id,
            )

        return redirect(url_for("users_movies", user_id=user_id), 303)

    def update_movie_details(
        self,
        user_id: int,
        movie_id: int,
    ) -> Response | tuple[str, int]:
        """Update movie details for a user's favorite movie."""
        data = request.get_json(silent=True) or request.form.to_dict()

        if (
            not data
            or not isinstance(data, dict)
            or "new_title" not in data
            or not str(data["new_title"]).strip()
        ):
            return redirect(
                url_for(
                    "users_movies",
                    user_id=user_id,
                    error=API_ERR_INVALID_REQUEST_DATA,
                ),
                303,
            )

        # Check if the user and movie exist
        user = self.data_manager.get_user_by_id(user_id)
        movie = self.data_manager.get_movie_by_id(movie_id)

        if not user or not movie:
            return (
                render_template("404.html", error=API_ERR_404_NOT_FOUND),
                404,
            )

        # Update the movie details
        movie.name = str(data["new_title"]).strip()

        self.data_manager.save_object(movie)

        return redirect(url_for("users_movies", user_id=user_id), 303)

    def delete_favorite_movie(
        self,
        user_id: int,
        movie_id: int,
    ) -> Response | tuple[str, int]:
        """Remove a movie from a user's favorites."""
        user = self.data_manager.get_user_by_id(user_id)
        movie = self.data_manager.get_movie_by_id(movie_id)

        if not user or not movie:
            return (
                render_template("404.html", error=API_ERR_404_NOT_FOUND),
                404,
            )

        self.data_manager.delete_favorite(user_id=user_id, movie_id=movie_id)
        return redirect(url_for("users_movies", user_id=user_id), 303)

    def fetch_omdb_data(self, movie_name: str) -> dict | None:
        """Fetch movie data from the OMDb API by title."""
        try:
            response = requests.get(
                OMBD_URL,
                params={"t": movie_name, "apikey": self.api_key},
                timeout=15,
            )
            data = response.json()
        except (requests.RequestException, ValueError):
            return {"error": OMBD_ERR_MSG}

        if not isinstance(data, dict):
            return {"error": OMBD_ERR_MSG}
        if response.status_code == STATUS_200_OK:
            if data.get("Response") == "True":
                return {
                    "title": data.get("Title"),
                    "year": data.get("Year"),
                    "director": data.get("Director"),
                    "poster_url": data.get("Poster"),
                    "imdb_id": data.get("imdbID"),
                }
            return {"error": data.get("Error", OMBD_ERR_MSG)}
        return {"error": OMBD_ERR_MSG}

    def search_ombd_by_title(self, title: str) -> dict | None:
        """Search for a movie by title using the OMDb API."""
        try:
            response = requests.get(
                OMBD_URL,
                params={"s": title, "apikey": self.api_key},
                timeout=15,
            )
            data = response.json()
        except (requests.RequestException, ValueError):
            return {"error": OMBD_ERR_MSG}

        if not isinstance(data, dict):
            return {"error": OMBD_ERR_MSG}
        if response.status_code == STATUS_200_OK:
            if data.get("Response") == "True":
                return data.get("Search", [])
            return {"error": data.get("Error", OMBD_ERR_MSG)}
        return {"error": OMBD_ERR_MSG}

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
        year="2010",
        poster_url="https://example.com/inception.jpg",
        imdb_id="tt1375666",
    )
    movie2 = Movie(
        name="The Matrix",
        director="The Wachowskis",
        year="1999",
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
