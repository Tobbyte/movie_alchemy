# 🎬 Movie Alchemy

Movie Alchemy is a small Flask web app for keeping personal movie collections.
Create users, search movies through the [OMDb API](https://www.omdbapi.com/),
add them to a user's shelf, attach a private note to each favorite, and remove
them again. Data is stored in SQLite via SQLAlchemy 2.0.

## Features

- Multiple users, each with their own movie shelf
- Movie search by title; pick the exact result from OMBd search and it is saved by its IMDb ID
- Movie infos like poster, director, year from OMBd are saved.
- Personal note (max. 500 characters) per favorite, editable inline
- Movie details can be changed per user and are saved as overrides on that
  user's favorite.
- Users can delete their account and all associated favorites.
- Server-side rendered pages
- Rate limiting: 100 requests per minute per IP address (Flask-Limiter)


## Project structure

```text
.d
├── app.py          # MovieAlchemyApp: routes, error handlers, OMDb requests
├── config.py       # Constants: DB path, OMDb URL, limits, user-facing messages
├── datamanager.py  # DataManager: all CRUD operations
├── models.py       # SQLAlchemy models: User, Movie, UsersFavorite
├── setup_db.py     # DB: engine, session factory, SQLite foreign key pragma
├── templates/
│   ├── base.html   # Layout
│   ├── index.html  # User list + "create user" form
│   ├── movies.html # A user's shelf, search and suggestions, notes
│   ├── 404.html
│   └── 500.html
├── static/
│   └── style.css
├── data/           # SQLite file is created here automatically
└── .env            # Your OMDb API key
```

## Getting started

### 1. Get an OMDb API key

Request a free key at <https://www.omdbapi.com/apikey.aspx>.

### 2. Install

```bash
git clone <your-repo-url>
cd movie_alchemy

pip install -r requirements.txt
```

### 3. Configure

Create a `.env` file in the project root:

```env
OMDB_API_KEY=your_key_here
```

The app refuses to start if the variable is missing.

### 4. Run

```bash
python app.py
```

Open <http://127.0.0.1:5000>. The database file `data/movie_alchemy.sqlite`
and all tables are created automatically on the first start.

> **Note:** There are no migrations. If you change a model (for example by
> adding a column), delete `data/movie_alchemy.sqlite` and restart. Calling
> `DB().reset_db()` drops and recreates all tables as well. Both remove all
> stored data.


## Routes

| Method     | Path                                       | Purpose                                  |
| ---------- | ------------------------------------------ | ---------------------------------------- |
| GET        | `/`                                        | Start page with all users                |
| GET / POST | `/users`                                   | List users / create a user               |
| GET / POST | `/users/<user_id>/movies`                  | Show a shelf / search OMDb by title      |
| POST       | `/users/<user_id>/movies_save`             | Save a selected search result (`imdb_id`) |
| POST       | `/users/<user_id>/movies/<movie_id>/update` | Update a favorite's details and note     |
| POST       | `/users/<user_id>/movies/<movie_id>/delete` | Remove a movie from a user's favorites   |
| POST       | `/users/<user_id>/delete`                   | Delete a user and their favorites        |

Successful `POST` requests redirect with `303 See Other`
(Post/Redirect/Get), so reloading a page never resubmits a form.

## Data model

| Table        | Columns                                                                                  |
| ------------ | ---------------------------------------------------------------------------------------- |
| `users`      | `id` (PK), `name` (unique)                                                                |
| `movies`     | `id` (PK), `name`, `director`, `year` (text, OMDb may return ranges), `poster_url`, `imdb_id` |
| `user_favs`  | `user_id` (PK, FK → users), `movie_id` (PK, FK → movies), `created_at`, `note`           |

`user_favs` is the association table between users and movies. Foreign keys
use `ON DELETE CASCADE`, and SQLite enforces them because
`PRAGMA foreign_keys=ON` is set for every connection (`setup_db.py`).

## Design notes

- **Separation of concerns:** `app.py` only handles HTTP and OMDb, the
  `DataManager` is the only place that talks to the database.
- **Sessions:** every `DataManager` method opens its own short transaction with
  `session_factory.begin()`. `expire_on_commit=False` keeps returned objects
  readable after the session is closed.
- **Error handling:** database errors are wrapped in `RuntimeError`
  (`DuplicateUserError` for taken names) and rendered as friendly HTML pages.
  OMDb failures (network, timeout, unknown movie) are shown on the shelf page.
- **OMDb requests** use `params=` (URL-encoded), HTTPS and a 15-second timeout.

## Known limitations

- No authentication: anyone can open any user's shelf.
- No CSRF protection on the POST forms (Flask-WTF `CSRFProtect` would be the
  next step).
- No database migrations.
- The development server (`debug=True`) is not meant for production use.
- The free OMDb key has a daily request limit.

## Ideas for the future

- Authentication and per-user sessions
- Alembic migrations
- Search results with pagination and filtering by type
- Ratings and "watched" status per favorite
- Tests...


## Acknowledgement

- Made with ❤️ and without ai or code completion (except this readme or where otherwise explicitly stated).