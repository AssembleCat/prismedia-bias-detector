import pandas as pd
import os
import re

class ExcelConverter:
    """엑셀 파일을 CSV로 변환하는 클래스"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = os.path.join(self.base_dir, 'data')
    
    def validate_news_id(self, df):
        """뉴스 식별자 유효성 검사 및 수정
        
        형식: '언론사코드.YYYYMMDDHHmmSSnnn'
        예: '02100801.20240331103032001'
        """
        if '뉴스 식별자' not in df.columns:
            raise ValueError("'뉴스 식별자' 컬럼이 없습니다.")
        
        def fix_news_id(row):
            news_id = str(row['뉴스 식별자'])
            # 소수점 형식으로 변환된 경우 처리 (예: 1100801.202401031 -> "1100801.202401031")
            if '.' in news_id and 'e' not in news_id.lower():  # 지수 표기법 제외
                try:
                    parts = news_id.split('.')
                    if len(parts) == 2:
                        return f"{parts[0]}.{parts[1]}"
                except:
                    pass
            
            # 기존 형식 검사 (언론사코드.YYYYMMDDHHmmSSnnn)
            pattern = r'^(\d{8})\.(\d{14}\d*)$'
            match = re.match(pattern, news_id)
            
            if match:
                media_code, timestamp = match.groups()
                return news_id
            else:
                # 날짜만 있는 경우 처리 (언론사코드.YYYYMMDD)
                date_pattern = r'^(\d{8})\.(\d{8})$'
                date_match = re.match(date_pattern, news_id)
                
                if date_match:
                    media_code, date = date_match.groups()
                    return f"{media_code}.{date}000001"
                
                # 잘못된 형식인 경우 로그 출력
                print(f"잘못된 뉴스 식별자 형식: {news_id}")
                return None
        
        df['뉴스 식별자'] = df.apply(fix_news_id, axis=1)
        
        # 유효하지 않은 식별자를 가진 행 제거
        invalid_rows = df['뉴스 식별자'].isna()
        if invalid_rows.any():
            print(f"유효하지 않은 식별자를 가진 {invalid_rows.sum()}개의 행이 제거되었습니다.")
            df = df.dropna(subset=['뉴스 식별자'])
        
        return df

    def process_single_file(self, excel_file):
        """단일 엑셀 파일 처리"""
        print(f"\n{'='*50}")
        print(f"파일 처리 시작: {excel_file}")
        print('='*50)
        
        excel_path = os.path.join(self.data_dir, excel_file)
        csv_path = os.path.join(self.data_dir, f"{os.path.splitext(excel_file)[0]}.csv")
        
        try:
            print("\n1. 엑셀 파일 읽기...")
            df = pd.read_excel(
                excel_path,
                dtype={
                    '뉴스 식별자': str,
                    '일자': str  # 일자를 문자열로 읽기
                }
            )
            
            print("\n2. 데이터프레임 기본 정보:")
            print(df.info())
            
            print("\n3. '뉴스 식별자' 컬럼 분석:")
            if '뉴스 식별자' in df.columns:
                print(f"- 전체 행 수: {len(df)}")
                print(f"- Null 값 수: {df['뉴스 식별자'].isna().sum()}")
                print(f"- 데이터 타입: {df['뉴스 식별자'].dtype}")
                print("\n처음 10개 레코드:")
                print("-" * 80)
                for idx, value in df['뉴스 식별자'].head(10).items():
                    print(f"[{idx}] 값: {value}")
                    print(f"    - 타입: {type(value)}")
                    print(f"    - 문자열 길이: {len(str(value))}")
                    print(f"    - repr: {repr(value)}")
                    print("-" * 80)
            else:
                print("'뉴스 식별자' 컬럼이 없습니다!")
                return False
            
            # 날짜 형식 변환
            if '일자' in df.columns:
                print("\n4. '일자' 컬럼 처리:")
                print("변환 전 처음 5개 값:", df['일자'].head().tolist())
                
                # 정수형 날짜를 문자열로 변환 (예: 20240101 -> "2024-01-01")
                df['일자'] = df['일자'].apply(lambda x: f"{str(x)[:4]}-{str(x)[4:6]}-{str(x)[6:8]}")
                print("변환 후 처음 5개 값:", df['일자'].head().tolist())
            
            # 뉴스 식별자 검증 및 수정
            print("\n5. 뉴스 식별자 검증 시작...")
            df = self.validate_news_id(df)
            
            # 검증 후 상태 확인
            print("\n6. 검증 후 처음 10개 레코드:")
            print("-" * 80)
            for idx, value in df['뉴스 식별자'].head(10).items():
                print(f"[{idx}] {value}")
            print("-" * 80)
            
            # CSV로 저장
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print(f"\n7. CSV 저장 완료: {csv_path}")
            print(f"   - 최종 처리된 행 수: {len(df)}")
            return True
            
        except Exception as e:
            print(f"\n오류 발생 ({excel_file}): {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False

    def convert_all_files(self):
        """모든 엑셀 파일을 CSV로 변환"""
        excel_files = [f for f in os.listdir(self.data_dir) if f.endswith('.xlsx')]
        
        if not excel_files:
            print("변환할 엑셀 파일이 없습니다.")
            return
        
        success_count = 0
        failed_files = []
        
        for excel_file in excel_files:
            if self.process_single_file(excel_file):
                success_count += 1
            else:
                failed_files.append(excel_file)
        
        print("\n=== 변환 작업 완료 ===")
        print(f"총 파일 수: {len(excel_files)}개")
        print(f"성공: {success_count}개")
        print(f"실패: {len(failed_files)}개")
        
        if failed_files:
            print("\n실패한 파일 목록:")
            for file in failed_files:
                print(f"- {file}")

def main():
    converter = ExcelConverter()
    response = input("엑셀 파일 변환을 진행하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        converter.convert_all_files()

if __name__ == "__main__":
    main()
