# pylint: disable=no-member
"""Module for managing database operations."""

from copy import copy

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from models import Movie, User, UsersFavorite
from setup_db import DB


class DuplicateUserError(RuntimeError):
    """Raised when a user name already exists."""


class DataManager:
    """Class to manage database CRUD operations."""

    def __init__(self) -> None:
        """Initialize the DataManager with a database instance."""
        self.db = DB()
        self.db.create_tables()

    def create_user(self, name: str) -> User:
        """Create a new user and add it to the database."""
        try:
            with self.db.session_factory.begin() as session:
                new_user = User(name=name)
                session.add(new_user)
        except IntegrityError as error:
            err_msg = "User name already exists."
            raise DuplicateUserError(err_msg) from error
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

    def get_favorite_movies(
        self,
        user_id: int,
    ) -> list[tuple]:
        """Retrieve a user's favorite movies and notes."""
        try:
            with self.db.session_factory.begin() as session:
                statement = (
                    select(Movie, UsersFavorite)
                    .join(UsersFavorite, UsersFavorite.movie_id == Movie.id)
                    .where(UsersFavorite.user_id == user_id)
                    .order_by(UsersFavorite.created_at.desc())
                )
                favorites = []
                for movie, favorite in session.execute(statement).all():
                    display_movie = copy(movie)
                    display_movie.name = favorite.name or display_movie.name
                    display_movie.director = (
                        favorite.director
                        if favorite.director is not None
                        else display_movie.director
                    )
                    display_movie.year = (
                        favorite.year
                        if favorite.year is not None
                        else display_movie.year
                    )
                    display_movie.poster_url = (
                        favorite.poster_url
                        if favorite.poster_url is not None
                        else display_movie.poster_url
                    )
                    display_movie.imdb_id = (
                        favorite.imdb_id
                        if favorite.imdb_id is not None
                        else display_movie.imdb_id
                    )
                    favorites.append((display_movie, favorite.note))
                return favorites
        except SQLAlchemyError as error:
            err_msg = "Failed to retrieve favorite movies."
            raise RuntimeError(err_msg) from error

    def add_movie_to_favorites(self, user_id: int, data: dict) -> None:
        """Add a movie and its favorite relationship atomically."""
        try:
            with self.db.session_factory.begin() as session:
                movies = list(
                    session.scalars(
                        select(Movie).where(Movie.imdb_id == data["imdb_id"]),
                    ).all(),
                )
                movie = next(
                    (
                        m
                        for m in movies
                        if session.get(
                            UsersFavorite,
                            (user_id, m.id),
                        )
                    ),
                    movies[0] if movies else None,
                )
                if movie is None:
                    movie = Movie(
                        name=data["title"],
                        year=data["year"],
                        director=data.get("director"),
                        poster_url=data.get("poster_url"),
                        imdb_id=data["imdb_id"],
                    )
                    session.add(movie)
                    session.flush()

                if session.get(UsersFavorite, (user_id, movie.id)) is None:
                    session.add(
                        UsersFavorite(
                            user_id=user_id,
                            movie_id=movie.id,
                        ),
                    )
        except SQLAlchemyError as error:
            err_msg = "Failed to save favorite movie."
            raise RuntimeError(err_msg) from error

    def update_movie(
        self,
        user_id: int,
        movie_id: int,
        movie_data: dict[str, str | None],
        note: str | None,
    ) -> bool:
        """Update a movie and its details per user."""
        try:
            with self.db.session_factory.begin() as session:
                favorite = session.scalars(
                    select(UsersFavorite).where(
                        UsersFavorite.user_id == user_id,
                        UsersFavorite.movie_id == movie_id,
                    ),
                ).one_or_none()
                if favorite:
                    movie = session.get(Movie, movie_id)
                    if movie is None:
                        return False
                    for field_name in (
                        "name",
                        "director",
                        "year",
                        "poster_url",
                        "imdb_id",
                    ):
                        value = movie_data[field_name]
                        setattr(
                            favorite,
                            field_name,
                            None
                            if value == getattr(movie, field_name)
                            else value,
                        )
                    favorite.note = note
                    return True
                return False
        except SQLAlchemyError as error:
            err_msg = "Failed to update favorite movie."
            raise RuntimeError(err_msg) from error

    def delete_favorite(self, user_id: int, movie_id: int) -> bool:
        """Remove a movie from a user's favorites."""
        try:
            with self.db.session_factory.begin() as session:
                favorite = session.scalars(
                    select(UsersFavorite).where(
                        UsersFavorite.user_id == user_id,
                        UsersFavorite.movie_id == movie_id,
                    ),
                ).one_or_none()
                if favorite:
                    session.delete(favorite)
                    return True
                return False
        except SQLAlchemyError as error:
            err_msg = "Failed to delete favorite movie."
            raise RuntimeError(err_msg) from error

    def delete_user(self, user_id: int) -> bool:
        """Delete a user and their associated favorites."""
        try:
            with self.db.session_factory.begin() as session:
                user = session.scalars(
                    select(User).where(User.id == user_id),
                ).one_or_none()
                if user:
                    session.delete(user)
                    return True
                return False
        except SQLAlchemyError as error:
            err_msg = "Failed to delete user."
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
