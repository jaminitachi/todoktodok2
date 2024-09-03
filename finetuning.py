import json
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from datasets import Dataset

# JSON 데이터 로드
with open('crawled_articles.json', 'r', encoding='utf-8') as f:
    articles = json.load(f)

# 데이터셋 준비
texts = [f"토론 주제: {article['title']}\n내용: {article['content']}" for article in articles]
dataset = Dataset.from_dict({"text": texts})

# 모델 및 토크나이저 초기화 (한국어 모델 사용)
model_name = "skt/kogpt2-base-v2"  # 또는 다른 적절한 한국어 모델
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# 데이터 전처리
def preprocess_function(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=512)

tokenized_dataset = dataset.map(preprocess_function, batched=True)

# 학습 설정
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    save_steps=1000,
    save_total_limit=2,
)

# 트레이너 초기화 및 학습
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

trainer.train()

# 모델 저장
model.save_pretrained("./fine_tuned_debate_model")
tokenizer.save_pretrained("./fine_tuned_debate_model")