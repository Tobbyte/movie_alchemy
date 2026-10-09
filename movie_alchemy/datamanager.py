"""Module for managing database operations."""

from models import Movie, User, UsersFavorite
from setup_db import DB
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError


class DataManager:
    """Class to manage database CRUD operations."""

    def __init__(self) -> None:
        """Initialize the DataManager with a database instance."""
        self.db = DB()

    def create_user(self, name: str) -> User:
        """Create a new user and add it to the database."""
        try:
            with self.db.session_factory.begin() as session:
                new_user = User(name=name)
                session.add(new_user)
        except SQLAlchemyError as error:
            err_msg = "Failed to create user."
            raise RuntimeError(err_msg) from error
        return new_user

    def get_users(self) -> list[User]:
        """Retrieve all users from the database."""
        try:
            with self.db.session_factory.begin() as session:
                return list(session.scalars(select(User)).all())
        except SQLAlchemyError as error:
            err_msg = "Failed to retrieve users from the database."
            raise RuntimeError(err_msg) from error

    def get_user_by_id(self, user_id: int) -> User | None:
        """Retrieve a user by their ID."""
        try:
            with self.db.session_factory.begin() as session:
                return session.scalars(
                    select(User).where(User.id == user_id),
                ).one_or_none()
        except SQLAlchemyError as error:
            err_msg = "Failed to retrieve user."
            raise RuntimeError(err_msg) from error

    def get_movies(self) -> list[Movie]:
        """Retrieve all movies from the database."""
        try:
            with self.db.session_factory.begin() as session:
                return list(session.scalars(select(Movie)).all())
        except SQLAlchemyError as error:
            err_msg = "Failed to retrieve movies."
            raise RuntimeError(err_msg) from error

    def get_movie_by_id(self, movie_id: int) -> Movie | None:
        """Retrieve a movie by its ID."""
        try:
            with self.db.session_factory.begin() as session:
                return session.scalars(
                    select(Movie).where(Movie.id == movie_id),
                ).one_or_none()
        except SQLAlchemyError as error:
            err_msg = "Failed to retrieve movie."
            raise RuntimeError(err_msg) from error

    def get_favorite_movies(self, user_id: int) -> list[Movie]:
        """Retrieve a user's favorite movies."""
        try:
            with self.db.session_factory.begin() as session:
                statement = (
                    select(Movie)
                    .join(UsersFavorite, UsersFavorite.movie_id == Movie.id)
                    .where(UsersFavorite.user_id == user_id)
                )
                return list(session.scalars(statement).all())
        except SQLAlchemyError as error:
            err_msg = "Failed to retrieve favorite movies."
            raise RuntimeError(err_msg) from error

    def delete_movie_by_id(self, movie_id: int) -> None:
        """Delete a movie by its ID."""
        try:
            with self.db.session_factory.begin() as session:
                movie_to_delete = session.scalars(
                    select(Movie).where(Movie.id == movie_id),
                ).one_or_none()
                if movie_to_delete:
                    session.delete(movie_to_delete)
        except SQLAlchemyError as error:
            err_msg = "Failed to delete movie."
            raise RuntimeError(err_msg) from error

    def save_object(self, obj: User | Movie | UsersFavorite) -> None:
        """Save a User or Movie object to the database."""
        try:
            with self.db.session_factory.begin() as session:
                session.add(obj)
        except SQLAlchemyError as error:
            err_msg = "Failed to save database object."
            raise RuntimeError(err_msg) from error

    def add_favorite(self, user_id: int, movie_id: int) -> None:
        """Add a movie to a user's favorites."""
        try:
            with self.db.session_factory.begin() as session:
                favorite = UsersFavorite(user_id=user_id, movie_id=movie_id)
                session.add(favorite)
        except SQLAlchemyError as error:
            err_msg = "Failed to save favorite movie."
            raise RuntimeError(err_msg) from error

    def add_movie(
        self,
        name: str,
        director: str | None = None,
        year: str | None = None,
        poster_url: str | None = None,
        imdb_id: str | None = None,
    ) -> Movie:
        """Add a new movie to the database."""
        try:
            with self.db.session_factory.begin() as session:
                new_movie = Movie(
                    name=name,
                    director=director,
                    year=year,
                    poster_url=poster_url,
                    imdb_id=imdb_id,
                )
                session.add(new_movie)
        except SQLAlchemyError as error:
            err_msg = "Failed to add movie."
            raise RuntimeError(err_msg) from error
        return new_movie
