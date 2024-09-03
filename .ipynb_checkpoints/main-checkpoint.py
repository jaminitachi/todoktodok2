import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic
import sys
import io

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
api_key = os.getenv("claude_api_key")
if not api_key:
    raise ValueError("API key not found. Make sure it's set in your .env file.")

client = Anthropic(api_key=api_key)

# JSON 파일에서 토론 주제 데이터 로드
with open('debate_topics.json', 'r', encoding='utf-8') as f:
    debate_topics = json.load(f)
with open('characters.json', 'r', encoding='utf-8') as f:
    debate_characters = json.load(f)
    
about_debate = """
1. 가치논제는 옳은지 그른지, 바람직한지 아닌지, 좋은지 나쁜지 등 가치판단이 쟁점이 되는 논제입니다. 승패를 가를 때에는 논제를 더 잘 이해하고, 적절한 근거를 잘 제시했는지를 평가하게 됩니다.
2. 반론/반박의 전략은 두 가지가 있습니다. 1)직접적/공격적으로 주장을 하는 방법은 상대방이 주장하고 제시한 내용들을 모두 반박하는 것입니다. 이런 방법을 취하기 위해서는 주장을 ‘잘’ 들을 수 있어야 하고, 주장에 대해 ‘적절하게’ 반박할 수 있어야 합니다. 2)방어적으로 주장을 하는 방법은 부정측의 입장을 토대로 주장을 세우고 시작하는 것입니다.
3. 토론에서 이기기 위해 가장 중요한 것은 상대방의 주장을 논파해내는 것이 아니라, 내 주장을 설득하는 것입니다. 아무리 허점을 찾아 공격해도 상대방이 자신의 생각이 틀렸다고 인정할 가능성은 현저하게 낮고, 청중의 입장에서도 양 측이 서로 나름대로 근거를 가지고 주장을 펼치고 있다고 생각을 할 것입니다. 토론의 진짜 의의는 ‘승패’보다도 “주제에 대해 충분히 생각해보고, 보다 나은 의사결정을 하는 것”에 있습니다.
"""

debate_template = """
1. 친구의 말 중 부적절한 부분이 있다면 반론의 전략 1번(직접적/공격적으로 주장을 하는 방법)을 사용하세요.
2. 친구의 주장이 적절하다면 반론의 전략 2번(방어적으로 주장을 하는 방법)을 사용하세요.
"""

analysis_prompt_template = """
친구가 방금 이렇게 말했어요:
"{user_input}"
{ai_role}에서, 길게 말하기보다는, 주장과 근거가 담긴 한문단 정도로 간결하게 반말로 답하세요. 앞서 말한 주장을 계속하여 반복하지 마세요.
"""

def select_debate_char():
    print("함께 토론할 캐릭터를 선택해주세요:")
    for i, ai_char in enumerate(debate_characters['characters'], 1):
        print(f"{i}. {ai_char['char_type']}")
    
    while True:
        try:
            choice = int(input("번호를 입력하세요: ")) - 1
            if 0 <= choice < len(debate_characters['characters']):
                return debate_characters["characters"][choice]
            else:
                print("올바른 번호를 입력해주세요.")
        except ValueError:
            print("숫자를 입력해주세요.")

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

def generate_initial_prompt(char, topic, user_stance):
    ai_stance = get_ai_stance(user_stance)
    ai_role = topic['stances'][ai_stance]
    ai_char = char
    return f"""당신은 중학생을 상대로 {ai_role}의 역할로 "{topic['topic']}"라는 주제로 토론하고 있습니다. 
    당신의 성격: 당신은 {ai_char['char_type']} 말투를 사용합니다. {ai_char['char_info']['personality']} {ai_char['char_info']['style']}
다음의 예시를 참고하세요. 사용자(논리적) "{ai_char['few_shot'][0]['user']}", 당신 "{ai_char['few_shot'][0]['bot']}" / 사용자(비논리적) "{ai_char['few_shot'][1]['user']}", 당신 "{ai_char['few_shot'][1]['bot']}"
이 말투와 예시를 참고하여 대화를 이어가세요.
    다음을 인식하세요: {about_debate}
    다음 지침을 따르세요: {debate_template}"""

def generate_analysis_prompt(topic, user_stance, user_input):
    ai_stance = get_ai_stance(user_stance)
    ai_role = topic['stances'][ai_stance]
    return analysis_prompt_template.format(user_input=user_input, ai_role=ai_role)

def chat_with_claude(user_input, char, topic, user_stance):
    global messages
    
    analysis_prompt = generate_analysis_prompt(topic, user_stance, user_input)
    messages.append({"role": "user", "content": analysis_prompt})
    
    # 시스템 메시지를 제외한 대화 내역만 전송
    chat_messages = [msg for msg in messages if msg["role"] != "system"]
    
    stream = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=500,
        messages=chat_messages,
        system=generate_initial_prompt(char, topic, user_stance),  # 매 요청마다 시스템 메시지 새로 생성
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

def main():
    global messages  # messages를 전역 변수로 선언
    
    selected_char = select_debate_char()
    selected_topic = select_debate_topic()
    user_stance = get_user_stance()
    ai_stance = get_ai_stance(user_stance)
    
    # 초기 시스템 메시지는 저장하지 않음
    messages = []
    
    print(f"\n캐릭터: {selected_char['char_type']}")
    print(f"토론 주제: {selected_topic['topic']}")
    print(f"당신의 입장: {user_stance}")
    print(f"AI의 입장: {ai_stance}")
    print("\n편하게 대화하듯이 의견을 나눠보세요. 대화를 끝내려면 '종료'를 입력하세요.")
    
    for _ in range(15):
        user_input = input("\n당신: ").encode('utf-8').decode('utf-8')
        if user_input.lower() == '종료':
            break
        
        chat_with_claude(user_input, selected_char, selected_topic, user_stance)
    
    print("\n오늘 대화 재밌었어! 또 이야기 나누자~")

if __name__ == "__main__":
    main()