import feedparser
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
from typing import List, Dict
import json

class NewsCrawler:
    def __init__(self):
        self.rss_feeds = {
            '조선일보': 'https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml',
            '한겨레': 'https://www.hani.co.kr/rss/',
            '중앙일보': 'https://rss.joins.com/joins_news_list.xml',
            '동아일보': 'https://www.donga.com/news/rss/rss.xml',
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def parse_article_content(self, url: str) -> str:
        """기사 URL에서 본문 내용을 추출합니다."""
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 대부분의 뉴스 사이트는 article 태그나 특정 클래스에 본문을 담고 있습니다
            article = soup.find('article') or soup.find(class_=['article_body', 'article-content', 'news_body'])
            if article:
                return article.get_text(strip=True)
            return ""
        except Exception as e:
            print(f"Error parsing article content from {url}: {str(e)}")
            return ""

    def collect_news(self) -> List[Dict]:
        """모든 뉴스사의 RSS 피드에서 기사를 수집합니다."""
        all_articles = []
        
        for press, rss_url in self.rss_feeds.items():
            try:
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries:
                    article = {
                        'press': press,
                        'title': entry.title,
                        'link': entry.link,
                        'published': entry.published,
                        'category': entry.get('category', ''),
                        'content': self.parse_article_content(entry.link)
                    }
                    all_articles.append(article)
                    
            except Exception as e:
                print(f"Error collecting news from {press}: {str(e)}")
                
        return all_articles

    def save_to_csv(self, articles: List[Dict], filename: str = 'news_data.csv'):
        """수집된 기사를 CSV 파일로 저장합니다."""
        df = pd.DataFrame(articles)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"Saved {len(articles)} articles to {filename}")

    def save_to_json(self, articles: List[Dict], filename: str = 'news_data.json'):
        """수집된 기사를 JSON 파일로 저장합니다."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(articles)} articles to {filename}")

if __name__ == "__main__":
    crawler = NewsCrawler()
    articles = crawler.collect_news()
    
    # CSV와 JSON 형식으로 저장
    crawler.save_to_csv(articles)
    crawler.save_to_json(articles)
