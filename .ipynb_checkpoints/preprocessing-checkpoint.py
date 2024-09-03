import json

# JSON 파일 로드
with open('crawled_articles.json', 'r', encoding='utf-8') as f:
    articles = json.load(f)

# 삭제할 인덱스 리스트 (0부터 시작)
indices_to_remove = [1, 2, 3, 4, 5]

# 역순으로 정렬하여 삭제 (뒤에서부터 삭제해야 앞의 인덱스에 영향을 주지 않음)
for index in sorted(indices_to_remove, reverse=True):
    del articles[index]

# 남은 항목들 재정렬 (필요한 경우)
for i, article in enumerate(articles):
    article['id'] = i + 1  # 1부터 시작하는 새로운 ID 부여

# 수정된 데이터를 새 JSON 파일로 저장
with open('cleaned_articles.json', 'w', encoding='utf-8') as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)

print(f"Cleaned data saved to 'cleaned_articles.json'. Total articles: {len(articles)}")