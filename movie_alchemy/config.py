"""Configuration for the Movie Alchemy app."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent  # project root
DB_PATH = PROJECT_ROOT / "data" / "movie_alchemy.sqlite"

STATUS_200_OK = 200
OMBD_URL = "https://www.omdbapi.com/"
OMBD_KEY_NOT_SET_ERROR = "OMDB_API_KEY environment variable is not set."
OMBD_ERR_MSG = "There was an error at OMDb, try again later."
LIMITER_DEFAULT_LIMIT = "100 per minute"
MAX_FAVORITE_NOTE_LENGTH = 500

API_ERR_INVALID_REQUEST_DATA = "Invalid request data"
API_ERR_DUPLICATE_USER = (
    "That user name is already taken. Try again with another name."
)
API_ERR_TOO_MANY_REQUESTS = "Too many requests"
API_ERR_INTERNAL_SERVER_ERROR = "Internal server error"
API_ERR_404_NOT_FOUND = "404 Not found"
API_ERR_METHOD_NOT_ALLOWED = "Method not allowed"
