"""Module to set up the database for the movie_alchemy project."""

import sqlite3
import sys
from pathlib import Path
from typing import Any

from movie_alchemy.models import Base
from sqlalchemy import (
    create_engine,
    event,
)
from sqlalchemy.orm import (
    sessionmaker,
)

# make runnable from wherever.
PROJECT_ROOT = Path(__file__).resolve().parent  # project root
sys.path.insert(0, str(PROJECT_ROOT.parent))


class DB:
    """Class to manage the database connection and session."""

    def __init__(self) -> None:
        """Initialize the database connection and session."""
        self.engine = create_engine(
            f"sqlite:///{PROJECT_ROOT / Path('data/movie_alchemy.sqlite')}",
        )
        self.session = sessionmaker(bind=self.engine)

        event.listen(self.engine, "connect", self.set_sqlite_pragma)

    def set_sqlite_pragma(
        self,
        dbapi_connection: sqlite3.Connection,
        _: Any,
    ) -> None:
        """Set PRAGMA foreign_keys=ON for each connection."""
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    def create_tables(self) -> None:
        """Create tables in the database."""
        Base.metadata.create_all(self.engine)
