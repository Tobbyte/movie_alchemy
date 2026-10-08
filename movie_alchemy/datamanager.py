"""Module for managing database operations."""

from models import Movie, User
from setup_db import db
from sqlalchemy import select


class DataManager:
    """Class to manage database CRUD operations."""

    def create_user(self, name: str) -> None:
        """Create a new user and add it to the database."""
        with db.session_factory.begin() as session:
            new_user = User(name=name)
            session.add(new_user)
            session.commit()

    def get_users(self) -> list[User]:
        """Retrieve all users from the database."""
        with db.session_factory.begin() as session:
            return list(session.scalars(select(User)).all())

    def get_movies(self) -> list[Movie]:
        """Retrieve all movies from the database."""
        with db.session_factory.begin() as session:
            return list(session.scalars(select(Movie)).all())

    def get_movie_by_id(self, movie_id: int) -> Movie | None:
        """Retrieve a movie by its ID."""
        with db.session_factory.begin() as session:
            return session.scalars(
                select(Movie).where(Movie.id == movie_id),
            ).one_or_none()

    def delete_movie_by_id(self, movie_id: int) -> None:
        """Delete a movie by its ID."""
        with db.session_factory.begin() as session:
            movie_to_delete = session.scalars(
                select(Movie).where(Movie.id == movie_id),
            ).one_or_none()
            if movie_to_delete:
                session.delete(movie_to_delete)
                session.commit()

    def save_object(self, obj: User | Movie) -> None:
        """Save a User or Movie object to the database."""
        with db.session_factory.begin() as session:
            session.add(obj)
            session.commit()

    def add_movie(
        self,
        name: str,
        director: str | None = None,
        year: int | None = None,
        poster_url: str | None = None,
        imdb_id: str | None = None,
    ) -> None:
        """Add a new movie to the database."""
        with db.session_factory.begin() as session:
            new_movie = Movie(
                name=name,
                director=director,
                year=year,
                poster_url=poster_url,
                imdb_id=imdb_id,
            )
            session.add(new_movie)
            session.commit()
