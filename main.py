import argparse
from csv_processor import CSVProcessor
from issue_extractor import extract_main_issues

def main():
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description='뉴스 기사 처리 및 이슈 추출')
    subparsers = parser.add_subparsers(dest='command', help='수행할 작업')
    
    # CSV 저장 명령어
    save_parser = subparsers.add_parser('save', help='CSV 파일을 DB에 저장')
    save_parser.add_argument('--pattern', default='*.csv', help='CSV 파일 패턴 (예: *.csv, news_*.csv)')
    
    # 이슈 추출 명령어
    issue_parser = subparsers.add_parser('issues', help='주요 이슈 추출')
    issue_parser.add_argument('--start-date', required=True, help='시작 날짜 (YYYY-MM-DD)')
    issue_parser.add_argument('--end-date', required=True, help='종료 날짜 (YYYY-MM-DD)')
    issue_parser.add_argument('--category', required=True, choices=['정치', '경제', '사회'], help='카테고리')
    issue_parser.add_argument('--n-issues', type=int, default=10, help='추출할 이슈 개수')
    
    args = parser.parse_args()
    
    if args.command == 'save':
        # CSV 파일 DB 저장
        processor = CSVProcessor()
        processor.process_files(args.pattern)
    
    elif args.command == 'issues':
        # 주요 이슈 추출
        issues = extract_main_issues(
            args.start_date,
            args.end_date,
            args.category,
            args.n_issues
        )

if __name__ == "__main__":
    main()
