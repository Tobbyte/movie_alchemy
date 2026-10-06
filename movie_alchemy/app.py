"""Movie Alchemy app."""

from movie_alchemy.models import Movie, User, UsersFavorite
from movie_alchemy.setup_db import DB
from sqlalchemy import or_, select

movie1 = Movie(name="m1name")
movie2 = Movie(name="m2name")
user1 = User(name="u1name")
user2 = User(name="u2name")


db = DB()
# db.create_tables()

with db.session.begin() as session:
    # session.add(movie1)
    # session.add(movie2)
    # session.add(user1)
    # session.add(user2)
    pass

with db.session.begin() as session:
    m1 = session.scalars(
        select(Movie).where(
            Movie.name == "m1name",
        ),
    ).first()  # could be multiple
    u1 = session.scalars(
        select(User).where(
            User.name == "u1name",
        ),
    ).one_or_none()
    print(m1, u1)
    if m1 and u1:
        like1 = UsersFavorite(u1.id, m1.id)
        session.add(like1)


with db.session.begin() as session:
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


# if __name__ == "__main__":
#     pass
