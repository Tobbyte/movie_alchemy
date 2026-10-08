"""Movie Alchemy app."""

from sqlalchemy import or_, select

from movie_alchemy.models import Movie, User, UsersFavorite
from movie_alchemy.setup_db import DB

db = DB()


def main():

    movie1 = Movie(name="m1name")
    movie2 = Movie(name="m2name")
    user1 = User(name="u1name")
    user2 = User(name="u2name")

    with db.session_factory.begin() as session:
        session.add(movie1)
        session.add(movie2)
        session.add(user1)
        session.add(user2)

    with db.session_factory.begin() as session:
        m1 = session.scalars(
            select(Movie).where(
                Movie.name == "m1name",
            ),
        ).one()

        u1 = session.scalars(
            select(User).where(
                User.name == "u1name",
            ),
        ).one_or_none()

        print(m1, u1)
        if m1 and u1:
            like1 = UsersFavorite(u1.id, m1.id)
            session.add(like1)

    with db.session_factory.begin() as session:
        result = session.scalars(select(User)).all()
        print(result)
        result = session.scalars(select(UsersFavorite)).all()
        print(result)

        movie1 = session.scalars(
            select(Movie).where(
                Movie.id == 1,
            ),
        ).one()
        print(movie1)
        # session.delete(movie1)


if __name__ == "__main__":
    db.reset_db()
    main()
