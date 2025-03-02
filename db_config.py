from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from models import Base

# DB 연결 설정
DATABASE_URL = "postgresql://newsuser:newspass@localhost:5432/newsdb"
engine = create_engine(DATABASE_URL)

def get_session():
    """데이터베이스 세션 생성"""
    Session = sessionmaker(bind=engine)
    return Session()

def ensure_table_exists():
    """테이블이 없을 경우에만 생성"""
    inspector = inspect(engine)
    if not inspector.has_table('news_articles'):
        Base.metadata.create_all(engine)
