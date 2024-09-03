import requests
from bs4 import BeautifulSoup
import time
import re
from transformers import BertTokenizer
import json

def preprocess_text(text):
    # HTML 태그 제거
    text = re.sub(r'<.*?>', '', text)
    # 특수 문자 제거
    text = re.sub(r'[^\w\s]', '', text)
    # 여러 개의 공백을 하나로 치환
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_article_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    title = soup.find('h1', class_='entry-title').text.strip()
    content = soup.find('div', class_='entry-content').text.strip()
    
    # 전처리 적용
    title = preprocess_text(title)
    content = preprocess_text(content)
    
    return title, content

def crawl_debate_site():
    base_url = "http://www.realdebate.co.kr/category/%ed%86%a0%eb%a1%a0%ec%9e%90%eb%a3%8c%ec%8b%a4/%ed%86%a0%eb%a1%a0%ea%b5%90%ec%9c%a1/page/{}/"
    
    all_articles = []
    
    for page in range(1, 12):  # 1부터 11페이지까지
        url = base_url.format(page)
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = soup.find_all('article', itemtype="http://schema.org/BlogPosting")
        
        for article in articles:
            article_url = article.find('h1', class_='entry-title').find('a')['href']
            title, content = get_article_content(article_url)
            
            all_articles.append({
                'title': title,
                'content': content,
                'url': article_url
            })
        
        print(f"Processed page {page}")
        time.sleep(1)  # 웹사이트에 부담을 주지 않기 위해 1초 대기
    
    return all_articles

if __name__ == "__main__":
    articles = crawl_debate_site()
    
    # 결과 출력 (예시)
    for i, article in enumerate(articles, 1):
        print(f"Article {i}:")
        print(f"Title: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Content preview: {article['content'][:100]}...")  # 내용 일부만 출력
        print("\n")

    print(f"Total articles crawled: {len(articles)}")

    # 크롤링한 데이터를 JSON 파일로 저장
    with open('crawled_articles.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print("Crawled data has been saved to 'crawled_articles.json'")