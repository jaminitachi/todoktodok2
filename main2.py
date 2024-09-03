import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import sys
import io
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
api_key = os.getenv("gpt_api_key")
if not api_key:
    raise ValueError("API key not found. Make sure it's set in your .env file.")

client = OpenAI(api_key=api_key)

# JSON 파일에서 토론 주제 데이터 로드
with open('debate_topics.json', 'r', encoding='utf-8') as f:
    debate_topics = json.load(f)

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

def generate_initial_prompt(topic, user_stance):
    ai_stance = get_ai_stance(user_stance)
    ai_role = topic['stances'][ai_stance]
    return f"""당신은 {ai_role}입니다. "{topic['topic']}"라는 주제로 친구와 대화를 나누고 있습니다.
{common_prompt}"""

def generate_analysis_prompt(topic, user_stance, user_input):
    ai_stance = get_ai_stance(user_stance)
    ai_role = topic['stances'][ai_stance]
    return analysis_prompt_template.format(user_input=user_input, ai_role=ai_role)

def chat_with_gpt(user_input, topic, user_stance):
    analysis_prompt = generate_analysis_prompt(topic, user_stance, user_input)
    messages.append({"role": "user", "content": analysis_prompt})
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": generate_initial_prompt(topic, user_stance)},
            *messages
        ],
        max_tokens=500,
        stream=True
    )
    
    print("GPT: ", end="", flush=True)
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_response += content
    
    print("\n")
    messages.append({"role": "assistant", "content": full_response})
    
    return full_response

# 메인 실행 부분
selected_topic = select_debate_topic()
user_stance = get_user_stance()
ai_stance = get_ai_stance(user_stance)

print(f"\n토론 주제: {selected_topic['topic']}")
print(f"당신의 입장: {user_stance}")
print(f"AI의 입장: {ai_stance}")
print("\n편하게 대화하듯이 의견을 나눠보세요. 대화를 끝내려면 '종료'를 입력하세요.")

messages = []

for i in range(15):
    user_input = input("\n당신: ").encode('utf-8').decode('utf-8')
    if user_input.lower() == '종료':
        break
    
    chat_with_gpt(user_input, selected_topic, user_stance)

print("\n오늘 대화 재밌었어! 또 이야기 나누자~")
