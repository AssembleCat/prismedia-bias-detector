from typing import Dict, List
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict

class BiasAnalyzer:
    def __init__(self):
        # 언론사 정치적 성향 데이터 (예시)
        self.press_bias = {
            '조선일보': 'conservative',
            '동아일보': 'conservative',
            '중앙일보': 'moderate',
            '한겨레': 'progressive'
        }
        
        # 이념적 키워드 사전 (예시)
        self.ideology_keywords = {
            'conservative': ['안보', '시장', '자유', '북한', '좌파', '종북', '일자리'],
            'progressive': ['복지', '평등', '노동', '민주', '개혁', '재벌', '서민']
        }

    def analyze_keyword_bias(self, text: str) -> Dict[str, float]:
        """텍스트에서 보수/진보 성향의 키워드 비율을 분석합니다."""
        text_words = set(text.split())
        
        scores = {
            'conservative': 0,
            'progressive': 0
        }
        
        for ideology, keywords in self.ideology_keywords.items():
            matched = sum(1 for keyword in keywords if keyword in text_words)
            scores[ideology] = matched / len(keywords) if matched > 0 else 0
            
        return scores

    def calculate_press_bias(self, articles: List[Dict]) -> Dict[str, Dict]:
        """각 언론사별 편향성 점수를 계산합니다."""
        press_scores = defaultdict(lambda: {'conservative': 0, 'progressive': 0, 'article_count': 0})
        
        for article in articles:
            press = article['press']
            content = article['content']
            
            # 기사 내용의 편향성 분석
            bias_scores = self.analyze_keyword_bias(content)
            
            press_scores[press]['conservative'] += bias_scores['conservative']
            press_scores[press]['progressive'] += bias_scores['progressive']
            press_scores[press]['article_count'] += 1
        
        # 평균 점수 계산
        for press in press_scores:
            article_count = press_scores[press]['article_count']
            if article_count > 0:
                press_scores[press]['conservative'] /= article_count
                press_scores[press]['progressive'] /= article_count
                
            # 편향성 지수 계산 (-1: 진보, 1: 보수)
            press_scores[press]['bias_index'] = (
                press_scores[press]['conservative'] - 
                press_scores[press]['progressive']
            )
        
        return dict(press_scores)

    def compare_article_bias(self, articles: List[Dict], topic: str = None) -> pd.DataFrame:
        """특정 주제에 대한 언론사별 보도 성향을 비교합니다."""
        if topic:
            # 특정 주제와 관련된 기사만 필터링
            filtered_articles = [
                article for article in articles 
                if topic.lower() in article['title'].lower() or topic.lower() in article['content'].lower()
            ]
        else:
            filtered_articles = articles
            
        press_bias = self.calculate_press_bias(filtered_articles)
        
        return pd.DataFrame.from_dict(press_bias, orient='index')

if __name__ == "__main__":
    # 테스트용 예시 데이터
    test_articles = [
        {
            'press': '조선일보',
            'title': '북한 도발 우려',
            'content': '안보 위기 속 북한의 도발이 우려된다. 자유 민주주의 수호가 중요하다.'
        },
        {
            'press': '한겨레',
            'title': '재벌 개혁 시급',
            'content': '경제 민주화와 재벌 개혁이 시급하다. 노동자의 권리 보호가 필요하다.'
        }
    ]
    
    analyzer = BiasAnalyzer()
    results = analyzer.compare_article_bias(test_articles)
    print(results)
