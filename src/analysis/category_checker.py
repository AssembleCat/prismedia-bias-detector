from utils.db_config import get_session
from models import NewsArticle

def check_categories():
    session = get_session()
    try:
        categories = session.query(NewsArticle.category1).distinct().all()
        print("\n=== 데이터베이스의 카테고리 목록 ===")
        for category in categories:
            print(category[0])
    finally:
        session.close()

if __name__ == "__main__":
    check_categories()
