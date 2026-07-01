from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
load_dotenv()

db_name=os.getenv('DB_NAME')
db_user= os.getenv('DB_USER')
password= os.getenv('DB_PASSWORD')
host= os.getenv('DB_HOST')
port=os.getenv('DB_PORT')


database_url=f'postgresql+psycopg2://{db_user}:{password}@{host}:{port}/{db_name}'
engine=create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()