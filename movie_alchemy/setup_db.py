"""Module to set up the database for the movie_alchemy project."""

import sqlite3
from typing import Any

from config import DB_PATH
from models import Base
from sqlalchemy import (
    create_engine,
    event,
)
from sqlalchemy.orm import (
    sessionmaker,
)


class DB:
    """Class to manage the database connection and session."""

    def __init__(self) -> None:
        """Initialize the database connection and session."""
        DB_PATH.parent.mkdir(exist_ok=True)
        self.engine = create_engine(f"sqlite:///{DB_PATH}")
        self.session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

        event.listen(self.engine, "connect", self.set_sqlite_pragma)

    def set_sqlite_pragma(
        self,
        dbapi_connection: sqlite3.Connection,
        _: Any,  # noqa: ANN401
    ) -> None:
        """Set PRAGMA foreign_keys=ON for each connection."""
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    def create_tables(self) -> None:
        """Create tables in the database."""
        Base.metadata.create_all(self.engine)

    def reset_db(self) -> None:
        """Reset the database by dropping and recreating tables."""
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)


if __name__ == "__main__":
    DB().create_tables()
