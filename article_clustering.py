from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
import numpy as np
from typing import List, Dict, Tuple
import pandas as pd
from datetime import datetime, timedelta

class ArticleClustering:
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens')
        
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """텍스트 리스트의 임베딩을 계산합니다."""
        return self.model.encode(texts, show_progress_bar=True)
    
    def cluster_articles(self, articles: List[Dict], 
                        eps: float = 0.3,
                        min_samples: int = 2,
                        time_window: int = 3) -> List[Dict]:
        """
        비슷한 주제의 기사들을 클러스터링합니다.
        
        Args:
            articles: 기사 목록
            eps: DBSCAN 클러스터링의 epsilon 값
            min_samples: 클러스터 형성에 필요한 최소 샘플 수
            time_window: 클러스터링할 때 고려할 시간 범위 (일)
        """
        # 날짜별로 기사 그룹화
        date_groups = self._group_by_date(articles, time_window)
        
        all_clusters = []
        cluster_id = 0
        
        for date_group in date_groups:
            if not date_group:
                continue
                
            # 제목과 본문의 일부를 결합하여 임베딩 생성
            texts = [
                f"{article['title']} {article['content'][:200]}"
                for article in date_group
            ]
            
            embeddings = self.get_embeddings(texts)
            
            # DBSCAN 클러스터링 수행
            clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(embeddings)
            
            # 클러스터링 결과 처리
            for idx, label in enumerate(clustering.labels_):
                if label == -1:  # 노이즈 포인트
                    continue
                    
                article = date_group[idx].copy()
                article['cluster_id'] = f"cluster_{cluster_id}_{label}"
                all_clusters.append(article)
            
            cluster_id += 1
        
        return all_clusters
    
    def _group_by_date(self, articles: List[Dict], window_days: int) -> List[List[Dict]]:
        """기사를 날짜 범위로 그룹화합니다."""
        # 날짜별로 기사 정렬
        dated_articles = []
        for article in articles:
            try:
                pub_date = datetime.strptime(article['published'], '%Y-%m-%d %H:%M:%S')
                dated_articles.append((pub_date, article))
            except:
                continue
        
        dated_articles.sort(key=lambda x: x[0])
        
        if not dated_articles:
            return []
            
        # 시간 윈도우로 그룹화
        groups = []
        current_group = []
        current_window_start = dated_articles[0][0]
        
        for date, article in dated_articles:
            if date - current_window_start <= timedelta(days=window_days):
                current_group.append(article)
            else:
                if current_group:
                    groups.append(current_group)
                current_group = [article]
                current_window_start = date
        
        if current_group:
            groups.append(current_group)
            
        return groups
    
    def analyze_clusters(self, clustered_articles: List[Dict]) -> pd.DataFrame:
        """클러스터링된 기사들을 분석합니다."""
        cluster_analysis = {}
        
        for article in clustered_articles:
            cluster_id = article['cluster_id']
            
            if cluster_id not in cluster_analysis:
                cluster_analysis[cluster_id] = {
                    'article_count': 0,
                    'press_distribution': {},
                    'titles': []
                }
            
            analysis = cluster_analysis[cluster_id]
            analysis['article_count'] += 1
            analysis['press_distribution'][article['press']] = \
                analysis['press_distribution'].get(article['press'], 0) + 1
            analysis['titles'].append(article['title'])
        
        # DataFrame으로 변환
        rows = []
        for cluster_id, analysis in cluster_analysis.items():
            row = {
                'cluster_id': cluster_id,
                'article_count': analysis['article_count'],
                'press_distribution': str(analysis['press_distribution']),
                'sample_titles': '\n'.join(analysis['titles'][:3])
            }
            rows.append(row)
            
        return pd.DataFrame(rows)

if __name__ == "__main__":
    # 테스트용 예시 데이터
    test_articles = [
        {
            'title': '코로나19 확진자 증가',
            'content': '오늘 코로나19 확진자가 100명 증가했다.',
            'press': '조선일보',
            'published': '2023-01-01 09:00:00'
        },
        {
            'title': '코로나 신규 확진 100명',
            'content': '코로나19 신규 확진자가 100명으로 집계됐다.',
            'press': '한겨레',
            'published': '2023-01-01 10:00:00'
        }
    ]
    
    clusterer = ArticleClustering()
    clusters = clusterer.cluster_articles(test_articles)
    analysis = clusterer.analyze_clusters(clusters)
    print(analysis)
