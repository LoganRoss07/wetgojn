from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+pymysql://admin:Password1@movieplatformdatabase.ct6m2rqy8ajq.us-east-1.rds.amazonaws.com:3306/movies"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit-False, autoflush=False, bind=engine)
