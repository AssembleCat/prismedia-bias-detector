from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from src.models.news_article import Base
import os

# 프로젝트 루트 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# SQLite DB 파일 경로 설정
DB_PATH = os.path.join(BASE_DIR, 'data', 'news.db')

# DB 파일이 저장될 디렉토리가 없으면 생성
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# SQLite DB 연결 설정
DATABASE_URL = f"sqlite:///{DB_PATH}"
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
