from datetime import datetime
from typing import Dict, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from konlpy.tag import Okt
from collections import defaultdict
from models import NewsArticle
from db_config import get_session

# 카테고리 상수 정의
CATEGORY_MAPPING = {
    "정치": {
        "정치>행정_자치",
        "정치>북한",
        "정치>국회_정당",
        "정치>외교",
        "정치>정치일반",
        "정치>선거",
        "정치>청와대"
    },
    "경제": {
        "경제>자원",
        "경제>부동산",
        "경제>금융_제테크",
        "경제>경제일반",
        "경제>자동차",
        "경제>반도체",
        "경제>산업_기업",
        "경제>무역",
        "경제>서비스_쇼핑",
        "경제>증권_증시",
        "경제>외환",
        "경제>취업_창업",
        "경제>유통",
        "경제>국제경제"
    },
    "사회": {
        "사회>의료_건강",
        "사회>환경",
        "사회>사건_사고",
        "사회>여성",
        "사회>장애인",
        "사회>날씨",
        "사회>노동_복지",
        "사회>사회일반",
        "사회>미디어",
        "사회>교육_시험"
    }
}

class IssueExtractor:
    """뉴스 기사에서 주요 이슈를 추출하는 클래스"""
    
    def __init__(self):
        """이슈 추출기 초기화"""
        self.session = get_session()
        self.okt = Okt()
        self.vectorizer = TfidfVectorizer(
            min_df=2,  # 최소 2개의 문서에서 등장해야 함
            max_df=0.9,  # 90% 이상의 문서에서 등장하는 단어는 제외
            tokenizer=self._tokenize
        )
    
    def _tokenize(self, text: str) -> List[str]:
        """텍스트를 형태소 분석하여 명사만 추출"""
        return self.okt.nouns(text)
    
    def _filter_articles(self, start_date: datetime.date, end_date: datetime.date, category: str) -> List[Tuple[str, str, str]]:
        """주어진 기간과 카테고리에 해당하는 기사 필터링"""
        query = self.session.query(
            NewsArticle.news_id,
            NewsArticle.title,
            NewsArticle.content
        ).filter(
            NewsArticle.date.between(start_date, end_date)
        )
        
        # 대분류 카테고리(정치, 경제, 사회)에 대한 처리
        if category in CATEGORY_MAPPING:
            subcategories = CATEGORY_MAPPING[category]
            query = query.filter(NewsArticle.category1.in_(subcategories))
        else:
            # 다른 카테고리의 경우 기존 로직 유지
            query = query.filter(NewsArticle.category1 == category)
        
        return [(article.news_id, article.title, article.content) for article in query.all()]
    
    def extract_issues(self, 
                      start_date: datetime.date,
                      end_date: datetime.date,
                      category: str,
                      n_issues: int = 10,
                      similarity_threshold: float = 0.3) -> Dict[str, List[str]]:
        """주요 이슈 추출
        
        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            category: 카테고리 (정치/경제/사회)
            n_issues: 추출할 이슈 개수
            similarity_threshold: 유사도 임계값
            
        Returns:
            {이슈 키워드: [관련 뉴스 ID 리스트]} 형태의 딕셔너리
        """
        try:
            # 기사 필터링
            articles = self._filter_articles(start_date, end_date, category)
            if not articles:
                return {}
                
            # 기사 ID와 텍스트 분리
            news_ids, titles, contents = zip(*articles)
            
            # 제목과 본문을 결합하여 TF-IDF 계산
            texts = [f"{title} {content}" for title, content in zip(titles, contents)]
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # 문서 간 유사도 계산
            similarities = cosine_similarity(tfidf_matrix)
            
            # 각 문서별로 유사한 문서 그룹화
            document_groups = defaultdict(set)
            for i in range(len(similarities)):
                for j in range(i + 1, len(similarities)):
                    if similarities[i, j] > similarity_threshold:
                        document_groups[i].add(j)
                        document_groups[j].add(i)
            
            # 그룹 크기순으로 정렬
            sorted_groups = sorted(
                document_groups.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
            
            # 주요 이슈 추출
            processed_docs = set()
            issues = {}
            
            for main_doc, similar_docs in sorted_groups:
                # 이미 처리된 문서는 건너뛰기
                if main_doc in processed_docs:
                    continue
                    
                # 현재 그룹의 모든 문서 ID
                group_docs = similar_docs | {main_doc}
                
                # 그룹 내 문서들의 TF-IDF 벡터 평균
                group_vector = tfidf_matrix[list(group_docs)].mean(axis=0)
                
                # 가장 중요한 단어 추출
                top_word_idx = group_vector.argmax()
                issue_keyword = self.vectorizer.get_feature_names_out()[top_word_idx]
                
                # 그룹 내 뉴스 ID 수집
                group_news_ids = [news_ids[i] for i in group_docs]
                
                # 결과 저장
                issues[issue_keyword] = group_news_ids
                
                # 처리된 문서 표시
                processed_docs.update(group_docs)
                
                # 원하는 이슈 개수에 도달하면 종료
                if len(issues) >= n_issues:
                    break
            
            return issues
            
        finally:
            self.session.close()

def extract_main_issues(start_date: str,
                       end_date: str,
                       category: str,
                       n_issues: int = 10) -> Dict[str, List[str]]:
    """주요 이슈 추출 함수
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD 형식)
        end_date: 종료 날짜 (YYYY-MM-DD 형식)
        category: 카테고리 (정치/경제/사회)
        n_issues: 추출할 이슈 개수
        
    Returns:
        {이슈 키워드: [관련 뉴스 ID 리스트]} 형태의 딕셔너리
    """
    # 날짜 문자열을 date 객체로 변환
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # 이슈 추출
    extractor = IssueExtractor()
    issues = extractor.extract_issues(start, end, category, n_issues)
    
    # 결과 출력
    print(f"\n=== 주요 이슈 추출 결과 ===")
    print(f"기간: {start_date} ~ {end_date}")
    print(f"카테고리: {category}")
    print(f"추출된 이슈 수: {len(issues)}")
    
    for keyword, news_ids in issues.items():
        print(f"\n[이슈 키워드] {keyword}")
        print(f"관련 기사 수: {len(news_ids)}")
        print(f"관련 기사 ID: {', '.join(news_ids[:5])}...")
    
    return issues
