from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = f"sqlite:///{BASE_DIR / 'bills.db'}"

class TrendingBill(Base):
    __tablename__ = 'trending_bills'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    rank = Column(Integer, nullable=False)
    count = Column(Integer, nullable=False)

# ✅ DB 초기화 함수 (테이블 생성용)
def init_ranking_db(db_path=DB_PATH):
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    print("✅ trending_bills 테이블이 초기화되었습니다.")
