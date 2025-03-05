import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from src.utils.db_config import get_session
from src.models import NewsArticle
from datetime import datetime

def check_articles():
    session = get_session()
    try:
        # 2024년 1월 데이터 조회
        start_date = datetime(2024, 1, 1).date()
        end_date = datetime(2024, 1, 31).date()
        
        # 전체 기사 수 확인
        total_count = session.query(NewsArticle).count()
        print(f"전체 기사 수: {total_count}")
        
        # 해당 기간 기사 수 확인
        period_count = session.query(NewsArticle).filter(
            NewsArticle.date.between(start_date, end_date)
        ).count()
        print(f"\n2024년 1월 기사 수: {period_count}")
        
        # 카테고리별 기사 수 확인
        categories = session.query(NewsArticle.category1).distinct().all()
        print("\n카테고리별 기사 수:")
        for category in categories:
            if category[0]:  # None이 아닌 경우만
                count = session.query(NewsArticle).filter(
                    NewsArticle.category1 == category[0],
                    NewsArticle.date.between(start_date, end_date)
                ).count()
                print(f"{category[0]}: {count}개")
                
        # 샘플 기사 확인
        print("\n샘플 기사:")
        sample = session.query(NewsArticle).filter(
            NewsArticle.date.between(start_date, end_date)
        ).first()
        if sample:
            print(f"ID: {sample.news_id}")
            print(f"제목: {sample.title}")
            print(f"날짜: {sample.date}")
            print(f"카테고리1: {sample.category1}")
            print(f"내용 길이: {len(sample.content) if sample.content else 0}")
            
    finally:
        session.close()

if __name__ == "__main__":
    check_articles()
