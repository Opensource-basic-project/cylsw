
# db 또는 새 함수를 만들어 통합적으로 main 대시보드에 필요한 정보를 가져오는 모듈


import requests
from bs4 import BeautifulSoup
from dbmanage_News import BillNews
from dbmanage_NewsReact import SessionLocal, NewsSentiment
from dash_news_app import create_dash_app_from_result
import urllib.request
import urllib.parse
import json
from collections import defaultdict
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from dbmanage_News import Bill


# 최신법안정보
# 속도가 빠르고, 실시간 정보가 중요하므로 main 실행 시마다 추출하도록 함 
def truncate(text, limit=10):
    return text[:limit] + "..." if len(text) > limit else text

def get_latest_laws(n=3):
    url = "https://www.law.go.kr/LSW/nwRvsLsPop.do?p_epubdt="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, headers=headers)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    tbody = soup.select_one("table.tbl3 > tbody")
    rows = tbody.find_all("tr")

    law_list = []

    for row in rows[:n]:  # 상위 n개만 추출
        columns = row.find_all("td")
        law_title_tag = columns[1].find("a")
        law_title = law_title_tag['title'].strip()

        # 전체 링크 조합
        href = law_title_tag['href'].strip()
        if not href.startswith("/"):
            href = "/" + href  # 슬래시 자동 보정

        detail_link = "https://www.law.go.kr" + href


        department = columns[2].get_text(strip=True)
        revision_type = columns[3].get_text(strip=True)
        proclaim_date = columns[6].get_text(strip=True)
        enforce_date = columns[7].get_text(strip=True)

        law_info = {
            "법안명": law_title,
            "법안명_truncated": truncate(law_title, 10),
            "소관부서": department,
            "제정/개정구분": revision_type,
            "공포일자": proclaim_date,
            "시행일자": enforce_date,
            "상세링크": detail_link
        }

        law_list.append(law_info)

    return law_list


# 메인-여론분석 블럭
def get_latest_news():
    session = SessionLocal()
    try:
        sentiment = session.query(NewsSentiment).order_by(NewsSentiment.analyzed_at.desc()).first()

        if sentiment:
            news = session.query(BillNews).filter_by(bill_id=sentiment.bill_id).first()

            pos = sentiment.positive_count or 0
            neg = sentiment.negative_count or 0
            neu = sentiment.neutral_count or 0
            total_comments = pos + neg + neu

            sentiment_data = {
                "title": (sentiment.title[:10] + "…") if news and len(sentiment.title) > 10 else (sentiment.title if news else "기사 제목 없음"),
                "news_bill_id": sentiment.id,
                "news_title": (news.news_title[:13] + "…") if news and len(news.news_title) > 13 else (news.news_title if news else "기사 제목 없음"),
                "news_body": (news.body[:200] + "…") if news and len(news.body) > 200 else (news.body if news else "기사 본문 없음"),
                "news_link": news.news_url if news else None,
                "comments": total_comments,
                "positive_count": pos,
                "negative_count": neg,
                "neutral_count": neu,
            }
            return sentiment_data
        else:
            return None
    except Exception as e:
        print(f"[ERROR] get_latest_news: {e}")
        return None
    finally:
        session.close()




#법안 랭킹
from dbmanage_News import Bill
from dbmanage_ranking import TrendingBill, Base, init_ranking_db  


# ------------------- DB 연결 -------------------
def get_session(db_path="sqlite:///bills.db"):
    engine = create_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()

# ------------------- 법안명 불러오기 -------------------
def get_law_keywords(session):
    bills = session.query(Bill.title).all()
    return [title for (title,) in bills]

# ------------------- 네이버 뉴스 API -------------------
client_id = "CKb4pAJ84D6tVcCvpjka"
client_secret = "5PucVvnteo"

headers = {
    "X-Naver-Client-Id": client_id,
    "X-Naver-Client-Secret": client_secret
}
base_url = "https://openapi.naver.com/v1/search/news.json"

def get_news_articles(query, start):
    url = f"{base_url}?query={urllib.parse.quote(query)}&display=100&start={start}&sort=date"
    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request)
    if response.getcode() == 200:
        return json.loads(response.read().decode("utf-8"))
    else:
        print(f"⚠️ API 호출 실패: HTTP Error {response.getcode()}")
        return None

# ------------------- 키워드 언급 수 세기 -------------------
def count_keyword_mentions(news_items, keyword):
    return sum(
        (item["title"] + item["description"]).lower().count(keyword.lower())
        for item in news_items
    )

# ------------------- 트렌딩 키워드 계산 -------------------
def calculate_trending_keywords(session):
    keywords = get_law_keywords(session)
    keyword_counts = defaultdict(int)

    for kw in keywords:
        print(f"🔍 '{kw}' 키워드 뉴스 검색 중...")
        result = get_news_articles(kw, 1)  # 뉴스 100개만
        if result and "items" in result:
            keyword_counts[kw] += count_keyword_mentions(result["items"], kw)

    return keyword_counts

# ------------------- 랭킹 출력 -------------------
def display_top_keywords(keyword_counts):
    sorted_counts = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    print("📊 최근 뉴스 기반 실시간 화제 법안 TOP 5")
    for i, (kw, count) in enumerate(sorted_counts[:5], 1):
        print(f"{i}. {kw} - 언급 {count}회")
    return sorted_counts[:5]

# ✅ 랭킹 저장 함수
def save_ranking_to_db(session, sorted_counts):
    session.query(TrendingBill).delete()
    for rank, (kw, count) in enumerate(sorted_counts[:5], 1):
        session.add(TrendingBill(title=kw, rank=rank, count=count))
    session.commit()
    print("✅ 랭킹 DB 저장 완료")

# ✅ 랭킹 조회 함수
def get_ranking(session):
    return session.query(TrendingBill).order_by(TrendingBill.rank).all()

# ------------------- 메인 -------------------
def main():
    init_ranking_db()  # 테이블 생성
    session = get_session()

    keyword_counts = calculate_trending_keywords(session)
    top_5 = display_top_keywords(keyword_counts)
    save_ranking_to_db(session, top_5)
    session.close()

if __name__ == "__main__":
        main()