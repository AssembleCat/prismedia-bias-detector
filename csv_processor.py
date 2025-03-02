import os
import glob
import pandas as pd
from datetime import datetime
from models import NewsArticle
from db_config import get_session, ensure_table_exists

class CSVProcessor:
    """CSV 파일 처리 클래스"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.base_dir, 'data')
    
    def process_single_file(self, csv_path, session, existing_news_ids):
        """단일 CSV 파일 처리
        
        Args:
            csv_path (str): CSV 파일 경로
            session: DB 세션
            existing_news_ids (set): 기존 뉴스 ID 집합
            
        Returns:
            tuple: (새로 저장된 기사 수, 건너뛴 기사 수)
        """
        print(f"\n처리 시작: {os.path.basename(csv_path)}")
        
        # CSV 파일 읽기
        df = pd.read_csv(csv_path)
        new_articles_count = 0
        skipped_count = 0
        
        # DataFrame의 각 행을 DB에 저장
        for idx, row in df.iterrows():
            # 진행상황 표시 (1000개마다)
            if idx > 0 and idx % 1000 == 0:
                print(f"  진행중: {idx}/{len(df)} 행 처리완료")
                
            try:
                # 날짜 형식 변환
                date = datetime.strptime(row['일자'], '%Y-%m-%d').date()
                
                # 뉴스 식별자가 이미 존재하는지 확인
                if row['뉴스식별자'] in existing_news_ids:
                    skipped_count += 1
                    continue
                    
                # 새 기사 객체 생성
                article = NewsArticle(
                    news_id=row['뉴스식별자'],
                    date=date,
                    media=row['언론사'],
                    author=row['기고자'],
                    title=row['제목'],
                    category1=row['분류1'],
                    category2=row['분류2'],
                    category3=row['분류3'],
                    people=row['인물'],
                    location=row['위치'],
                    organization=row['기관'],
                    keywords=row['키워드'],
                    characteristics=row['특성추출'],
                    content=row['본문'],
                    source=row['출처']
                )
                
                session.add(article)
                new_articles_count += 1
                existing_news_ids.add(row['뉴스식별자'])
                
                # 1000개마다 커밋
                if new_articles_count % 1000 == 0:
                    session.commit()
                    print(f"  중간 저장 완료: {new_articles_count}개 저장")
                    
            except Exception as e:
                print(f"  오류 발생 (행 {idx}): {str(e)}")
                continue
        
        # 마지막 커밋
        session.commit()
        print(f"파일 처리 완료: {os.path.basename(csv_path)}")
        print(f"  - 새로 저장된 기사: {new_articles_count}개")
        print(f"  - 건너뛴 기사: {skipped_count}개")
        
        return new_articles_count, skipped_count
    
    def process_files(self, csv_pattern="*.csv"):
        """여러 CSV 파일을 읽어서 DB에 저장
        
        Args:
            csv_pattern (str): CSV 파일 패턴 (예: "*.csv", "news_*.csv" 등)
        """
        # CSV 파일 목록 가져오기
        csv_pattern_path = os.path.join(self.data_dir, csv_pattern)
        csv_files = glob.glob(csv_pattern_path)
        
        if not csv_files:
            raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_pattern_path}")
        
        print(f"총 {len(csv_files)}개의 CSV 파일을 찾았습니다.")
        
        # 테이블 존재 확인
        ensure_table_exists()
        
        # 세션 생성
        session = get_session()
        
        try:
            # 기존 뉴스 ID 조회
            existing_news_ids = set(id_tuple[0] for id_tuple in session.query(NewsArticle.news_id).all())
            print(f"기존 DB에 저장된 기사 수: {len(existing_news_ids)}개")
            
            # 전체 처리 결과 집계
            total_new = 0
            total_skipped = 0
            
            # 각 CSV 파일 처리
            for csv_file in csv_files:
                try:
                    new_count, skipped_count = self.process_single_file(csv_file, session, existing_news_ids)
                    total_new += new_count
                    total_skipped += skipped_count
                except Exception as e:
                    print(f"파일 처리 실패 ({os.path.basename(csv_file)}): {str(e)}")
                    continue
            
            print("\n=== 전체 처리 결과 ===")
            print(f"처리된 파일 수: {len(csv_files)}개")
            print(f"새로 저장된 총 기사 수: {total_new}개")
            print(f"건너뛴 총 기사 수: {total_skipped}개")
            
        except Exception as e:
            session.rollback()
            print(f"오류 발생: {str(e)}")
            raise
        
        finally:
            session.close()
