from transformers import AutoTokenizer, AutoModel
from konlpy.tag import Mecab
from sklearn.feature_extraction.text import TfidfVectorizer
import torch
import numpy as np
from typing import List, Dict
import pandas as pd

class NLPProcessor:
    def __init__(self):
        # KoBERT 모델 로드
        self.tokenizer = AutoTokenizer.from_pretrained("monologg/kobert")
        self.model = AutoModel.from_pretrained("monologg/kobert")
        
        try:
            self.mecab = Mecab()
        except:
            print("Mecab 초기화 실패. 형태소 분석이 제한될 수 있습니다.")
            self.mecab = None

    def preprocess_text(self, text: str) -> str:
        """텍스트 전처리를 수행합니다."""
        if self.mecab:
            # Mecab을 이용한 형태소 분석
            morphs = self.mecab.morphs(text)
            return ' '.join(morphs)
        return text

    def get_bert_embedding(self, text: str) -> np.ndarray:
        """텍스트의 BERT 임베딩을 반환합니다."""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        # [CLS] 토큰의 임베딩을 사용
        embeddings = outputs.last_hidden_state[:, 0, :].numpy()
        return embeddings[0]

    def calculate_tfidf(self, texts: List[str]) -> pd.DataFrame:
        """텍스트 목록의 TF-IDF 행렬을 계산합니다."""
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english'
        )
        
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        
        return pd.DataFrame(
            tfidf_matrix.toarray(),
            columns=feature_names
        )

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """텍스트의 감성을 분석합니다."""
        # 여기서는 간단한 규칙 기반 감성 분석을 구현
        # 실제로는 감성 분석 모델을 사용하는 것이 좋습니다
        positive_words = set(['좋다', '훌륭하다', '긍정', '발전', '성공'])
        negative_words = set(['나쁘다', '실패', '부정', '문제', '위기'])
        
        preprocessed = self.preprocess_text(text)
        words = set(preprocessed.split())
        
        positive_score = len(words & positive_words) / len(positive_words)
        negative_score = len(words & negative_words) / len(negative_words)
        
        return {
            'positive': positive_score,
            'negative': negative_score,
            'neutral': 1 - (positive_score + negative_score)
        }

    def process_articles(self, articles: List[Dict]) -> pd.DataFrame:
        """뉴스 기사들을 처리하고 분석 결과를 반환합니다."""
        results = []
        
        for article in articles:
            preprocessed_content = self.preprocess_text(article['content'])
            sentiment = self.analyze_sentiment(preprocessed_content)
            embedding = self.get_bert_embedding(preprocessed_content)
            
            result = {
                'press': article['press'],
                'title': article['title'],
                'sentiment_positive': sentiment['positive'],
                'sentiment_negative': sentiment['negative'],
                'sentiment_neutral': sentiment['neutral'],
                'embedding': embedding
            }
            
            results.append(result)
            
        return pd.DataFrame(results)

if __name__ == "__main__":
    # 테스트용 예시 데이터
    test_articles = [
        {
            'press': '조선일보',
            'title': '경제 성장 전망',
            'content': '경제가 좋아지고 있다. 성공적인 정책이 효과를 보이고 있다.'
        },
        {
            'press': '한겨레',
            'title': '경제 위기 경고',
            'content': '경제 문제가 심각하다. 위기 상황이 계속되고 있다.'
        }
    ]
    
    processor = NLPProcessor()
    results = processor.process_articles(test_articles)
    print(results[['press', 'title', 'sentiment_positive', 'sentiment_negative']])
