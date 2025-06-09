# id title && 그래프에 대한 정보 매칭
# bill_id 는 통용되는 key 값이라 db 끼리 접근할때 꼭 필요
# title 은 가시성을 위해서 넣는 것 권장 

# dbmanage_NewsReact.py
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime


from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = f"sqlite:///{BASE_DIR / 'bills.db'}"

Base = declarative_base()
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class NewsSentiment(Base):
    __tablename__ = "news_sentiment"

    id = Column(Integer, primary_key=True, autoincrement=True) # index 역할
    bill_id = Column(Integer, nullable=False) # 법안 id
    title = Column(String) # 법안명
    news_url = Column(String, nullable=False) # 해당 법안에 대한 최다 댓글 기사 url
    positive_count = Column(Integer, default=0) # 긍정 수
    negative_count = Column(Integer, default=0) # 부정 수
    neutral_count = Column(Integer, default=0) # 중립 수 
    analyzed_at = Column(DateTime, default=datetime.utcnow) # 분석 일자 (db 갱신 일자)

    __table_args__ = (UniqueConstraint("bill_id", "news_url"),) # 같은 id, 기사 중복방지

class NewsComment(Base):
    __tablename__ = "news_comment"  # 댓글 저장 db

    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(Integer, nullable=False)
    news_url = Column(String, nullable=False)
    author = Column(String)
    date = Column(String)
    text = Column(Text)  # 댓글 내용
    like = Column(Integer, default=0)
    dislike = Column(Integer, default=0)
    type = Column(String)  # '부모' 또는 '답글' (의미 없음 : 자식댓글 수집 X)
    sentiment = Column(String)  # 감정분석 결과 컬럼

    __table_args__ = (UniqueConstraint("bill_id", "news_url", "author", "text"),)



#  외부에서 호출할 수 있는 초기화 함수
def init_sentiment_table():
    Base.metadata.create_all(bind=engine)
    print("DB 초기화 완료하였습니다.\n")


#  분석 여부 확인
def is_sentiment_already_analyzed(bill_id: int, news_url: str) -> bool:
    session = SessionLocal()
    try:
        return session.query(NewsSentiment).filter_by(bill_id=bill_id, news_url=news_url).first() is not None
    finally:
        session.close()



def insert_sentiment_result(bill_id: int, title: str, news_url: str, sentiment_counts: dict):
    session = SessionLocal()
    try:
        new_entry = NewsSentiment(
            bill_id=bill_id,
            title=title,
            news_url=news_url,  
            positive_count=sentiment_counts.get("긍정적 인식", 0),
            negative_count=sentiment_counts.get("부정적 인식", 0),
            neutral_count=sentiment_counts.get("중립", 0),
        )
        session.add(new_entry)
        session.commit()
        print(f"✅ 저장 완료: {bill_id} / {title}")
    except Exception as e:
        print(f"❌ 저장 실패: {bill_id} → {e}")
        session.rollback()
    finally:
        session.close()


def insert_news_comments(bill_id: int, news_url: str, comments: list[dict]):
    session = SessionLocal()
    try:
        for c in comments:
            session.add(NewsComment(
                bill_id=bill_id,
                news_url=news_url,
                author=c.get("작성자", ""),
                date=c.get("작성일자", ""),
                text=c.get("댓글", ""),
                like=c.get("공감수", 0),
                dislike=c.get("비공감수", 0),
                type=c.get("유형", "부모"),
                sentiment=c.get("감정", "중립")  
            ))
        session.commit()
        print(f"📝 댓글 {len(comments)}건 저장 완료")
    except Exception as e:
        print(f"❌ 댓글 저장 실패: {e}")
        session.rollback()
    finally:
        session.close()


