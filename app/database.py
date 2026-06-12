# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(
    "postgresql+psycopg2://postgres:111111@127.0.0.1:5432/ai_hr_pharma_db"
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()