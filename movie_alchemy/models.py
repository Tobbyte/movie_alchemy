"""Movie Alchemy Models."""
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    """Base class for declarative models."""


class User(Base):
    """Base class defining the users table."""

    __tablename__ = "users"

    def __init__(self, name: str) -> None:
        """Initialize the User instance."""
        self.name = name

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    def __repr__(self) -> str:
        """Create String representation."""
        return f"User(id: {self.id}, name: {self.name})"

    def __str__(self) -> str:
        """Create String representation."""
        return self.__repr__()

    def as_dict(self) -> dict:
        """Return a dictionary representation of the User instance."""
        return {
            "id": self.id,
            "name": self.name,
        }


class Movie(Base):
    """Base class defining the movies table."""

    __tablename__ = "movies"

    def __init__(
        self,
        name: str,
        director: str | None = None,
        year: str | None = None,  # data from ombd could be "2013-2014"
        poster_url: str | None = None,
        imdb_id: str | None = None,
    ) -> None:
        """Initialize the Movie instance."""
        self.name = name
        self.director = director
        self.year = year
        self.poster_url = poster_url
        self.imdb_id = imdb_id

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(String)
    director: Mapped[str | None] = mapped_column(String, default=None)
    year: Mapped[str | None] = mapped_column(String, default=None)
    poster_url: Mapped[str | None] = mapped_column(String, default=None)
    imdb_id: Mapped[str | None] = mapped_column(String, default=None)

    def __repr__(self) -> str:
        """Create String representation."""
        return f"Movie(id: {self.id}, name: {self.name})"

    def __str__(self) -> str:
        """Create String representation."""
        return self.__repr__()

    def as_dict(self) -> dict:
        """Return a dictionary representation of the Movie instance."""
        return {
            "id": self.id,
            "name": self.name,
            "director": self.director,
            "year": self.year,
            "poster_url": self.poster_url,
            "imdb_id": self.imdb_id,
        }

class UsersFavorite(Base):
    """Base class defining the users_favorites table."""

    __tablename__ = "user_favs"

    def __init__(self, user_id: int, movie_id: int) -> None:
        """Initialize the UsersFavorites instance."""
        self.user_id = user_id
        self.movie_id = movie_id

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        """Create String representation."""
        return f"Favorite(id: {self.user_id}, name: {self.movie_id})"

    def __str__(self) -> str:
        """Create String representation."""
        return self.__repr__()

    def as_dict(self) -> dict:
        """Return a dictionary representation of the User instance."""
        return {
            "user_id": self.user_id,
            "movie_id": self.movie_id,
        }
