from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///legislation.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# DB 테이블 구조 정의 
class LegislationNotice(Base):  #진행중 입법예고 
    __tablename__ = "legislation_notices"

    id = Column(Integer, primary_key=True, index=True)
    bill_name = Column(String)
    bill_no = Column(String, index=True)
    proposer = Column(String)
    bill_id = Column(String)
    noti_ed_dt = Column(String)
    link_url = Column(String)
    curr_committee = Column(String)
    announce_dt = Column(String)
    proposal_text = Column(String)

class EndedLegislationNotice(Base):  # 종료된 입법예고
    __tablename__ = "ended_legislation_notices"

    id = Column(Integer, primary_key=True, index=True)
    bill_name = Column(String)
    bill_no = Column(String, index=True)
    proposer = Column(String)
    bill_id = Column(String, index=True)
    noti_ed_dt = Column(String)
    link_url = Column(String)
    curr_committee = Column(String)
    announce_dt = Column(String)
    proposal_text = Column(String)

class PlenaryBill(Base):
    __tablename__ = "plenary_bills"

    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(String, index=True)
    bill_no = Column(String, index=True)
    bill_name = Column(String)
    proposer = Column(String)
    proc_result_cd = Column(String)
    link_url = Column(String)
    propose_dt = Column(String)      
    committee_nm = Column(String) 
    proposal_text = Column(String)
    
    so_committee_date = Column(String)
    so_committee_result = Column(String)
    law_committee_date = Column(String)
    law_committee_result = Column(String)
    plenary_vote_date = Column(String)
    plenary_vote_result = Column(String)
    
    
class ForeignLawTrend(Base):
    __tablename__ = "foreign_law_trends"

    cn = Column(String, primary_key=True, index=True) 
    title = Column(String)
    nation_name = Column(String)
    org_law_name = Column(String)
    procl_date = Column(String)
    asc_info = Column(String)
    detail_url = Column(String)
    proposal_text = Column(String)
    
class ForeignLawExample(Base):
    __tablename__ = "foreign_law_examples"
    id = Column(Integer, primary_key=True, index=True)
    cn = Column(String, unique=True, index=True)
    title = Column(String)
    rel_law = Column(String)
    asc_name = Column(String)
    issue_date = Column(String)
    detail_url = Column(String)
    proposal_text = Column(String)
    
def init_db():
    Base.metadata.create_all(bind=engine)
