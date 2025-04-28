from sqlmodel import create_engine, SQLModel

PATH_DB = "sqlite:///dancers.db"

engine = create_engine(PATH_DB)

def init_db():
    SQLModel.metadata.create_all(engine)