from app.database.connection import Base, engine

# Importing the models package registers every ORM model class on Base's
# metadata as a side effect. create_all() only knows about models that have
# been imported somewhere before it runs. Module 1 will add model classes
# here; until then this import is a no-op.
from app import models  # noqa: F401


def init_db():
    Base.metadata.create_all(bind=engine)
