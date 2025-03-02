from news_crawler import NewsCrawler
from bias_analyzer import BiasAnalyzer
from nlp_processor import NLPProcessor
from article_clustering import ArticleClustering
import pandas as pd
from datetime import datetime
import os

def main():
    # 결과를 저장할 디렉토리 생성
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    # 현재 시간을 파일명에 사용
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("1. 뉴스 기사 수집 중...")
    crawler = NewsCrawler()
    articles = crawler.collect_news()
    
    # 수집된 기사 저장
    articles_file = f'{output_dir}/articles_{timestamp}.json'
    crawler.save_to_json(articles, articles_file)
    print(f"- 수집된 기사를 {articles_file}에 저장했습니다.")
    
    print("\n2. 언론사 편향성 분석 중...")
    bias_analyzer = BiasAnalyzer()
    bias_results = bias_analyzer.compare_article_bias(articles)
    
    # 편향성 분석 결과 저장
    bias_file = f'{output_dir}/bias_analysis_{timestamp}.csv'
    bias_results.to_csv(bias_file)
    print(f"- 편향성 분석 결과를 {bias_file}에 저장했습니다.")
    print("\n언론사별 편향성 점수:")
    print(bias_results)
    
    print("\n3. 자연어 처리 분석 중...")
    nlp_processor = NLPProcessor()
    nlp_results = nlp_processor.process_articles(articles)
    
    # NLP 분석 결과 저장
    nlp_file = f'{output_dir}/nlp_analysis_{timestamp}.csv'
    nlp_results.to_csv(nlp_file)
    print(f"- NLP 분석 결과를 {nlp_file}에 저장했습니다.")
    
    print("\n4. 유사 기사 클러스터링 중...")
    clusterer = ArticleClustering()
    clustered_articles = clusterer.cluster_articles(articles)
    cluster_analysis = clusterer.analyze_clusters(clustered_articles)
    
    # 클러스터링 결과 저장
    cluster_file = f'{output_dir}/clusters_{timestamp}.csv'
    cluster_analysis.to_csv(cluster_file)
    print(f"- 클러스터링 결과를 {cluster_file}에 저장했습니다.")
    print("\n주요 기사 클러스터:")
    print(cluster_analysis[['cluster_id', 'article_count', 'sample_titles']])

if __name__ == "__main__":
    main()
