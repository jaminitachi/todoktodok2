import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic
import sys
import io
from transformers import AutoTokenizer, AutoModelForCausalLM

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
load_dotenv()

# Claude 설정
api_key = os.getenv("claude_api_key")
if not api_key:
    raise ValueError("API key not found. Make sure it's set in your .env file.")
client = Anthropic(api_key=api_key)

# 파인튜닝된 모델 로드
tokenizer = AutoTokenizer.from_pretrained("./fine_tuned_debate_model")
model = AutoModelForCausalLM.from_pretrained("./fine_tuned_debate_model")

# JSON 파일에서 토론 주제 데이터 로드
with open('debate_topics.json', 'r', encoding='utf-8') as f:
    debate_topics = json.load(f)

# 기존 프롬프트 템플릿들은 그대로 유지

common_prompt = """
다음 지침을 따르세요:
1. 친구와 대화하듯이 편안하고 자연스러운 말투로 대화하세요. 이왕이면 반말로 대화하세요.
2. 전문용어나 복잡한 표현은 피하고, 일상적인 언어를 사용하세요.
3. 상대방의 의견을 존중하면서도 당신의 생각을 솔직하게 표현하세요.
4. 개인적인 경험이나 주변 사례를 들어 설명해도 좋습니다.
5. 필요하다면 농담이나 비유를 사용해 대화를 부드럽게 이어가세요.
6. 상대방의 감정을 고려하면서도 당신의 입장을 명확히 전달하세요.
"""

analysis_prompt_template = """
친구가 방금 이렇게 말했어요:
"{user_input}"
{ai_role}에서, 친구와 대화하듯이 자연스럽게 응답해주세요. 다음 요소를 포함해보세요:
1. 친구의 말에 대한 간단한 반응 (공감이나 의견 차이 표현)
2. 당신의 생각을 일상적인 언어로 설명
3. 개인적인 경험이나 들어본 사례 언급 (적절하다면)
4. 친구에게 궁금한 점이나 생각해볼 만한 새로운 관점 제시
친구와 수다 떠는 것처럼 반말로 편하게 대화해주세요.
"""

def select_debate_topic():
    print("토론 주제를 선택해주세요:")
    for i, topic in enumerate(debate_topics, 1):
        print(f"{i}. {topic['keyword']}")
    
    while True:
        try:
            choice = int(input("번호를 입력하세요: ")) - 1
            if 0 <= choice < len(debate_topics):
                return debate_topics[choice]
            else:
                print("올바른 번호를 입력해주세요.")
        except ValueError:
            print("숫자를 입력해주세요.")

def get_user_stance():
    while True:
        stance = input("당신의 입장을 선택하세요 (찬성/반대): ").strip()
        if stance in ["찬성", "반대"]:
            return stance
        print("잘못된 입력입니다. '찬성' 또는 '반대'를 입력해주세요.")

def get_ai_stance(user_stance):
    return "반대" if user_stance == "찬성" else "찬성"

def generate_initial_response(topic, user_stance, user_input):
    ai_stance = get_ai_stance(user_stance)
    ai_role = topic['stances'][ai_stance]
    prompt = f"""토론 주제: {topic['topic']}
당신의 입장: {ai_role}
친구의 말: {user_input}
위 내용을 바탕으로 친구와 대화하듯이 자연스럽게 응답해주세요:"""

    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(**inputs, max_length=200, num_return_sequences=1, do_sample=True)
    initial_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return initial_response.split("응답해주세요:")[-1].strip()

def chat_with_claude(user_input, topic, user_stance):
    # 파인튜닝된 모델로 초기 응답 생성
    initial_response = generate_initial_response(topic, user_stance, user_input)
    
    # Claude에 전달할 분석 프롬프트 생성
    analysis_prompt = generate_analysis_prompt(topic, user_stance, user_input)
    messages.append({"role": "user", "content": analysis_prompt})
    
    # 파인튜닝된 모델의 응답을 Claude에 전달
    claude_prompt = f"""파인튜닝된 모델이 다음과 같이 응답했습니다:
"{initial_response}"
이 응답을 참고하여, 더 자연스럽고 대화에 적합한 응답을 생성해주세요."""
    
    messages.append({"role": "user", "content": claude_prompt})
    
    stream = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=500,
        messages=messages,
        system=generate_initial_prompt(topic, user_stance),
        stream=True
    )
    
    print("Claude: ", end="", flush=True)
    full_response = ""
    for event in stream:
        if event.type == "content_block_start":
            continue
        elif event.type == "content_block_delta":
            print(event.delta.text, end="", flush=True)
            full_response += event.delta.text
        elif event.type == "content_block_stop":
            break
    
    print("\n")
    messages.append({"role": "assistant", "content": full_response})
    
    return full_response

# 메인 실행 부분은 그대로 유지