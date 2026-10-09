"""Module for managing database operations."""

from models import Movie, User, UsersFavorite
from setup_db import DB
from sqlalchemy import select


class DataManager:
    """Class to manage database CRUD operations."""

    def __init__(self) -> None:
        """Initialize the DataManager with a database instance."""
        self.db = DB()

    def create_user(self, name: str) -> User:
        """Create a new user and add it to the database."""
        with self.db.session_factory.begin() as session:
            new_user = User(name=name)
            session.add(new_user)
        return new_user

    def get_users(self) -> list[User]:
        """Retrieve all users from the database."""
        try:
            with self.db.session_factory.begin() as session:
                return list(session.scalars(select(User)).all())
        except Exception as e:
            err_msg = "Failed to retrieve users from the database."
            raise RuntimeError(err_msg) from e

    def get_user_by_id(self, user_id: int) -> User | None:
        """Retrieve a user by their ID."""
        with self.db.session_factory.begin() as session:
            return session.scalars(
                select(User).where(User.id == user_id),
            ).one_or_none()

    def get_movies(self) -> list[Movie]:
        """Retrieve all movies from the database."""
        with self.db.session_factory.begin() as session:
            return list(session.scalars(select(Movie)).all())

    def get_movie_by_id(self, movie_id: int) -> Movie | None:
        """Retrieve a movie by its ID."""
        with self.db.session_factory.begin() as session:
            return session.scalars(
                select(Movie).where(Movie.id == movie_id),
            ).one_or_none()

    def delete_movie_by_id(self, movie_id: int) -> None:
        """Delete a movie by its ID."""
        with self.db.session_factory.begin() as session:
            movie_to_delete = session.scalars(
                select(Movie).where(Movie.id == movie_id),
            ).one_or_none()
            if movie_to_delete:
                session.delete(movie_to_delete)

    def save_object(self, obj: User | Movie | UsersFavorite) -> None:
        """Save a User or Movie object to the database."""
        with self.db.session_factory.begin() as session:
            session.add(obj)

    def add_favorite(self, user_id: int, movie_id: int) -> None:
        """Add a movie to a user's favorites."""
        with self.db.session_factory.begin() as session:
            favorite = UsersFavorite(user_id=user_id, movie_id=movie_id)
            session.add(favorite)

    def add_movie(
        self,
        name: str,
        director: str | None = None,
        year: str | None = None,
        poster_url: str | None = None,
        imdb_id: str | None = None,
    ) -> Movie:
        """Add a new movie to the database."""
        with self.db.session_factory.begin() as session:
            new_movie = Movie(
                name=name,
                director=director,
                year=year,
                poster_url=poster_url,
                imdb_id=imdb_id,
            )
            session.add(new_movie)
        return new_movie
