from sqlalchemy import Column, String, Date, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class NewsArticle(Base):
    """뉴스 기사 데이터베이스 모델"""
    __tablename__ = 'news_articles'

    news_id = Column(String, primary_key=True)
    date = Column(Date, nullable=False)
    media = Column(String)
    author = Column(String)
    title = Column(String)
    category1 = Column(String)
    category2 = Column(String)
    category3 = Column(String)
    people = Column(String)
    location = Column(String)
    organization = Column(String)
    keywords = Column(String)
    characteristics = Column(String)
    content = Column(Text)
    source = Column(String)
