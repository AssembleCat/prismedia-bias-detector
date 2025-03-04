import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime
from models import NewsArticle
from db_config import get_session, ensure_table_exists

class CSVProcessor:
    """CSV 파일 처리 클래스"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.base_dir, 'data')
    
    def convert_nan_to_empty(self, value):
        """NaN 값을 빈 문자열로 변환"""
        if pd.isna(value) or value == 'nan':
            return ''
        return str(value)
    
    def process_single_file(self, csv_path, session, existing_news_ids):
        """단일 CSV 파일 처리
        
        Args:
            csv_path (str): CSV 파일 경로
            session: DB 세션
            existing_news_ids (set): 기존 뉴스 ID 집합
            
        Returns:
            tuple: (새로 저장된 기사 수, 건너뛴 기사 수, 오류 발생 여부)
        """
        print(f"\n처리 시작: {os.path.basename(csv_path)}")
        
        error_occurred = False
        
        try:
            # CSV 파일 읽기 - 뉴스 식별자를 문자열로 읽기
            df = pd.read_csv(csv_path, dtype={'뉴스 식별자': str})
            
            # NaN 값을 빈 문자열로 변환
            for column in df.columns:
                df[column] = df[column].apply(self.convert_nan_to_empty)
            
            # 컬럼명 매핑
            column_mapping = {
                '뉴스 식별자': 'news_id',
                '일자': 'date',
                '언론사': 'media',
                '기고자': 'author',
                '제목': 'title',
                '통합 분류1': 'category1',
                '통합 분류2': 'category2',
                '통합 분류3': 'category3',
                '인물': 'people',
                '위치': 'location',
                '기관': 'organization',
                '키워드': 'keywords',
                '특성추출(가중치순 상위 50개)': 'characteristics',
                '본문': 'content',
                'URL': 'source'
            }
            
            # 컬럼명 변경
            df = df.rename(columns=column_mapping)
            
            new_articles_count = 0
            skipped_count = 0
            duplicate_count = 0
            
            # DataFrame의 각 행을 DB에 저장
            for idx, row in df.iterrows():
                # 진행상황 표시 (1000개마다)
                if idx > 0 and idx % 1000 == 0:
                    print(f"  진행중: {idx}/{len(df)} 행 처리완료")
                    
                try:
                    # 날짜 처리
                    try:
                        date = pd.to_datetime(row['date']).date()
                    except:
                        print(f"  날짜 변환 오류 (행 {idx}): {row['date']}")
                        skipped_count += 1
                        error_occurred = True
                        continue
                    
                    # 뉴스 식별자가 이미 존재하는지 확인
                    if str(row['news_id']) in existing_news_ids:
                        duplicate_count += 1
                        skipped_count += 1
                        continue
                    
                    # 새 기사 객체 생성
                    article = NewsArticle(
                        news_id=str(row['news_id']),
                        date=date,
                        media=self.convert_nan_to_empty(row['media']),
                        author=self.convert_nan_to_empty(row['author']),
                        title=self.convert_nan_to_empty(row['title']),
                        category1=self.convert_nan_to_empty(row['category1']),
                        category2=self.convert_nan_to_empty(row['category2']),
                        category3=self.convert_nan_to_empty(row['category3']),
                        people=self.convert_nan_to_empty(row['people']),
                        location=self.convert_nan_to_empty(row['location']),
                        organization=self.convert_nan_to_empty(row['organization']),
                        keywords=self.convert_nan_to_empty(row['keywords']),
                        characteristics=self.convert_nan_to_empty(row['characteristics']),
                        content=self.convert_nan_to_empty(row['content']),
                        source=self.convert_nan_to_empty(row['source'])
                    )
                    
                    session.add(article)
                    new_articles_count += 1
                    existing_news_ids.add(str(row['news_id']))
                    
                    # 1000개마다 커밋
                    if new_articles_count % 1000 == 0:
                        session.commit()
                        print(f"  중간 저장 완료: {new_articles_count}개 저장")
                        
                except Exception as e:
                    print(f"  오류 발생 (행 {idx}): {str(e)}")
                    skipped_count += 1
                    error_occurred = True
                    continue
            
            # 마지막 커밋
            session.commit()
            print(f"파일 처리 완료: {os.path.basename(csv_path)}")
            print(f"  - 새로 저장된 기사: {new_articles_count}개")
            print(f"  - 중복된 기사: {duplicate_count}개")
            print(f"  - 오류로 건너뛴 기사: {skipped_count - duplicate_count}개")
            print(f"  - 총 건너뛴 기사: {skipped_count}개")
            
            return new_articles_count, skipped_count, error_occurred
            
        except Exception as e:
            print(f"파일 처리 중 오류 발생: {str(e)}")
            return 0, 0, True
    
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
            existing_news_ids = set(str(id_tuple[0]) for id_tuple in session.query(NewsArticle.news_id).all())
            print(f"기존 DB에 저장된 기사 수: {len(existing_news_ids)}개")
            
            # 전체 처리 결과 집계
            total_new = 0
            total_skipped = 0
            error_files = []  # 예외가 발생한 파일
            skipped_files = []  # 건너뛴 기사나 중복이 있는 파일
            
            # 각 CSV 파일 처리
            for csv_file in csv_files:
                try:
                    new_count, skipped_count, error_occurred = self.process_single_file(csv_file, session, existing_news_ids)
                    total_new += new_count
                    total_skipped += skipped_count
                    
                    # 건너뛴 기사가 있는 경우
                    if skipped_count > 0:
                        skipped_files.append({
                            'file': os.path.basename(csv_file),
                            'skipped': skipped_count - (skipped_count if error_occurred else 0),  # 오류로 인한 건너뛰기 제외
                            'error_skipped': skipped_count if error_occurred else 0  # 오류로 인한 건너뛰기
                        })
                    
                    # 예외가 발생한 경우
                    if error_occurred:
                        error_files.append(os.path.basename(csv_file))
                        
                except Exception as e:
                    print(f"파일 처리 실패 ({os.path.basename(csv_file)}): {str(e)}")
                    error_files.append(os.path.basename(csv_file))
                    continue
            
            print("\n=== 전체 처리 결과 ===")
            print(f"처리된 파일 수: {len(csv_files)}개")
            print(f"새로 저장된 총 기사 수: {total_new}개")
            print(f"건너뛴 총 기사 수: {total_skipped}개")
            
            if error_files:
                print("\n=== 오류가 발생한 파일 목록 ===")
                for file in error_files:
                    print(f"- {file}")
            
            if skipped_files:
                print("\n=== 건너뛴 기사가 있는 파일 목록 ===")
                for file_info in skipped_files:
                    skipped_msg = []
                    if file_info['skipped'] > 0:
                        skipped_msg.append(f"중복/날짜오류: {file_info['skipped']}개")
                    if file_info['error_skipped'] > 0:
                        skipped_msg.append(f"처리오류: {file_info['error_skipped']}개")
                    print(f"- {file_info['file']} (건너뛴 기사: {', '.join(skipped_msg)})")
            
        except Exception as e:
            session.rollback()
            print(f"오류 발생: {str(e)}")
            raise
        
        finally:
            session.close()
