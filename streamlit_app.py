import streamlit as st
import logging
import os
import sys
from dotenv import load_dotenv
from main import DebateBot
import time
import traceback

# 로깅 설정 강화
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()

# 디버그 모드 설정
DEBUG_MODE = False

# 세션 상태 초기화 함수
def initialize_session_state():
    if 'debate_bot' not in st.session_state:
        api_key = os.getenv("claude_api_key")
        if not api_key:
            st.error("API key not found. Please set it in your .env file.")
            st.stop()
        st.session_state.debate_bot = DebateBot(api_key)
        logger.info("DebateBot initialized")

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'evaluation_result' not in st.session_state:
        st.session_state.evaluation_result = None

    if 'selected_topic' not in st.session_state:
        st.session_state.selected_topic = None

    if 'debate_started' not in st.session_state:
        st.session_state.debate_started = False

    if 'selected_char' not in st.session_state:
        st.session_state.selected_char = None

    if 'user_stance' not in st.session_state:
        st.session_state.user_stance = None

    if 'page' not in st.session_state:
        st.session_state.page = "select_topic"

# 세션 상태 초기화 실행
initialize_session_state()

# 초기 데이터 로드
st.session_state.debate_bot.load_data()

def get_styles():
    return """
    <style>
    .main {
        background-color: white;
    }
    .gray-text {
        color: gray;
    }
    .App {
        text-align: center;
        padding: 20px;
    }
    .title h1 {
        color: #0184FF;
    }
    .card {
        display: inline-block;
        width: 45%;
        margin: 10px;
        padding: 15px;
        border-radius: 15px;
        background-color: #F9F9F9;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .card img {
        width: 100%;
        border-radius: 10px;
        cursor: pointer;
    }
    .card h3 {
        margin: 10px 0;
        font-size: 20px;
        color: #333;
    }
    .card p {
        color: #555;
    }
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 20px;
        border-radius: 15px;
        background-color: #F0F0F0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    .message {
        padding: 10px;
        border-radius: 20px;
        margin: 10px 0;
        max-width: 70%;
        word-wrap: break-word;
        clear: both;
    }
    .you-message {
        background-color: #007BFF;
        color: white;
        float: right;
        box-shadow: 0px 2px 12px rgba(0, 123, 255, 0.5);
    }
    .ai-message {
        background-color: #F1F1F1;
        color: black;
        float: left;
        box-shadow: 0px 2px 12px rgba(0, 0, 0, 0.1);
    }
    .date-label {
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
        color: #888;
        font-size: 14px;
    }
    .evaluation-result {
        margin-top: 20px;
    }
    .evaluation-result h2 {
        color: #0184FF;
    }
    .evaluation-result p {
        margin: 10px 0;
        font-size: 16px;
    }
    </style>
    """

def get_header():
    return """
    <div style="text-align: center;">
        <h1 style="color: #0184FF;">TODOK</h1>
    </div>
    """

def display_message(sender, message):
    if sender == "You":
        return f'''
        <div class="message you-message">{message}</div>
        '''
    else:
        return f'''
        <div class="message ai-message">{message}</div>
        '''

def debug_info():
    if DEBUG_MODE:
        st.sidebar.title("Debug Information")
        st.sidebar.write("Session State:")
        st.sidebar.json(st.session_state)
        st.sidebar.write("Current Chat History:")
        st.sidebar.json(st.session_state.chat_history)

def show_topic_selection():
    st.markdown(get_styles(), unsafe_allow_html=True)
    st.markdown(get_header(), unsafe_allow_html=True)
    debug_info()

    char_options = [char['char_type'] for char in st.session_state.debate_bot.debate_characters['characters']]
    st.session_state.selected_char = st.selectbox("토론 상대의 말투를 선택해주세요:", char_options)

    topic_types = list(set([topic['type'] for topic in st.session_state.debate_bot.debate_topics]))
    selected_type = st.selectbox("토론 주제의 유형을 선택해주세요:", topic_types)

    filtered_topics = [topic for topic in st.session_state.debate_bot.debate_topics if topic['type'] == selected_type]
    
    st.markdown("토론하고 싶은 주제를 선택하세요", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    for i, topic in enumerate(filtered_topics):
        column = col1 if i % 2 == 0 else col2
        with column:
            st.image(topic["image_url"], use_column_width=True)
            st.markdown(f"**{topic['keyword']}**")
            if st.button(f"선택", key=f"select_{topic['keyword']}"):
                st.session_state.selected_topic = topic
                st.session_state.page = "topic_detail"
                st.rerun()  # 페이지 상태 변경 후 즉시 재실행


def show_topic_detail():
    st.markdown(get_styles(), unsafe_allow_html=True)
    st.markdown(get_header(), unsafe_allow_html=True)

    topic = st.session_state.selected_topic
    st.image(topic["image_url"], use_column_width=True)
    st.markdown(f"### {topic['keyword']}")
    st.markdown(topic['summary'])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("선택"):
            st.session_state.page = "chat"
            st.rerun()
    with col2:
        if st.button("뒤로가기"):
            st.session_state.selected_topic = None
            st.session_state.page = "select_topic"
            st.rerun()

def show_chat_interface():
    st.markdown(get_styles(), unsafe_allow_html=True)
    st.markdown(get_header(), unsafe_allow_html=True)
    
    st.markdown('<div class="date-label">2024년 8월 12일 월요일</div>', unsafe_allow_html=True)

    if st.session_state.selected_topic:
        st.session_state.user_stance = st.radio("당신의 입장을 선택하세요:", ["찬성", "반대"])

        if st.session_state.user_stance:
            if st.session_state.user_stance == "찬성":
                st.markdown(f'<p class="gray-text">당신은 "{st.session_state.selected_topic["topic"]}"에 찬성하셨습니다. 즐겁게 토론 해보세요.</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p class="gray-text">당신은 "{st.session_state.selected_topic["topic"]}"에 반대하셨습니다. 즐겁게 토론 해보세요.</p>', unsafe_allow_html=True)

        if st.button("토론 시작"):
            try:
                if st.session_state.selected_char and st.session_state.selected_topic:
                    st.session_state.debate_bot.start_debate(
                        st.session_state.selected_char,
                        st.session_state.selected_topic['keyword'],
                        st.session_state.user_stance
                    )
                    st.session_state.debate_started = True
                    st.session_state.chat_history = []
                    st.session_state.evaluation_result = None
                    logger.info("Debate started successfully")
            except Exception as e:
                st.error(f"토론을 시작하는 중 오류가 발생했습니다: {e}")
                logger.error(f"Error starting debate: {e}")
                if DEBUG_MODE:
                    st.error(f"Traceback: {traceback.format_exc()}")

    if st.session_state.debate_started:
        chat_history = st.container()
        with chat_history:
            for chat in st.session_state.chat_history:
                if chat['user']:
                    st.markdown(display_message("You", chat['user']), unsafe_allow_html=True)
                if chat['ai']:
                    st.markdown(display_message("AI", chat['ai']), unsafe_allow_html=True)

        with st.form(key='chat_form', clear_on_submit=True):
            if len(st.session_state.chat_history) >= 10:
                st.warning("입력 횟수 제한을 초과했습니다. 토론 종료버튼을 눌러서 토론 점수를 확인해보세요 !")
            length_warning = st.empty()
            user_input = st.text_input("당신의 의견을 입력하세요:", key="user_input")
            col1, col2 = st.columns([5, 1])
            
            with col1:
                submit_button = st.form_submit_button("전송")
            with col2:
                end_debate_button = st.form_submit_button("토론 종료")
        
        if submit_button and user_input.strip():
            if len(st.session_state.chat_history) < 10:
                if len(user_input) > 200:
                    length_warning.warning("입력 수를 초과했습니다. 조금 더 짧게 입력해주세요.")
                else:
                    st.session_state.chat_history.append({"user": user_input, "ai": ""})
                    chat_history.markdown(display_message("You", user_input), unsafe_allow_html=True)
                    ai_response_container = chat_history.empty()
                    try:
                        logger.info("대화 생성 시작")
                        ai_response = ""
                        start_time = time.time()
                        for chunk in st.session_state.debate_bot.chat_stream(user_input):
                            ai_response += chunk
                            ai_response_container.markdown(display_message("AI", ai_response), unsafe_allow_html=True)
                            if time.time() - start_time > 30:
                                logger.warning("API 응답 타임아웃")
                                raise TimeoutError("API 응답이 너무 오래 걸립니다.")
                        st.session_state.chat_history[-1]["ai"] = ai_response
                        logger.info("대화 생성 완료")
                    except TimeoutError as e:
                        st.error(f"대화 생성 중 타임아웃: {e}")
                        logger.error(f"TimeoutError: {e}")
                    except Exception as e:
                        st.error(f"대화 생성 중 오류가 발생했습니다: {e}")
                        logger.error(f"Error during chat generation: {e}", exc_info=True)
                        if DEBUG_MODE:
                            st.error(f"Traceback: {traceback.format_exc()}")
                        if "overloaded_error" in str(e):
                            st.warning("서버가 현재 과부하 상태입니다. 잠시 후 다시 시도해 주세요.")
        
        if end_debate_button:
            logger.info(f"Chat history before evaluation: {st.session_state.chat_history}")
            try:
                st.session_state.evaluation_result = st.session_state.debate_bot.evaluate_debate(st.session_state.chat_history)
                logger.info(f"Evaluation result: {st.session_state.debate_bot.evaluation_result}")
                st.session_state.debate_started = False
                logger.info("Debate ended and evaluated successfully")

                st.session_state.page = 'eval'
                logger.info("Changing page to eval")
                time.sleep(0.1)  # 상태 업데이트를 위한 짧은 지연
                st.rerun()

            except Exception as e:
                st.error(f"토론 평가 중 오류가 발생했습니다: {e}")
                logger.error(f"Error during debate evaluation: {e}", exc_info=True)
                if DEBUG_MODE:
                    st.error(f"Traceback: {traceback.format_exc()}")
                sys.stdout.flush()  # 예외 발생 시에도 로그 강제 플러시


def show_evaluation_page():
    logger.info("Entering show_evaluation_page")
    logger.info(f"Current evaluation result: {st.session_state.debate_bot.evaluation_result}")

    st.markdown(get_styles(), unsafe_allow_html=True)
    st.markdown(get_header(), unsafe_allow_html=True)

    if st.session_state.debate_bot.evaluation_result:
        result = st.session_state.debate_bot.evaluation_result
        logger.info(f"Displaying evaluation result: {result}")
        if "error" in result:
            st.error(f"평가 중 오류가 발생했습니다: {result['error']}")
            if "raw_response" in result:
                st.text(f"AI의 원본 응답: {result['raw_response']}")
        elif isinstance(result, dict) and all(key in result for key in ['주제의 일관성', '논리적 연결성', '반박의 적절성', '근거의 타당성', '총점']):
            st.subheader("토론 평가 결과")

            if isinstance(result['총점'], dict) and '점수' in result['총점']:
                st.markdown(f"**총점: {result['총점']['점수']} / 100**")
                if '개선방안' in result['총점']:
                    st.markdown(f"**총평: {result['총점']['개선방안']}**")
            else:
                st.markdown(f"**총점: {result['총점']} / 100**")

            st.markdown("### 세부 평가")
            categories = ['주제의 일관성', '논리적 연결성', '반박의 적절성', '근거의 타당성']
            scores = []

            for key in categories:
                if isinstance(result[key], dict):
                    score = result[key].get('점수', 'N/A')  # 기본 값 설정
                    improvement = result[key].get('개선을 위한 조언', 'N/A')  # 기본 값 설정
                    st.markdown(f"**{key} ({score} / 20)**")
                    st.markdown(f"- 개선방안: {improvement}")
                    scores.append(score)
                else:
                    st.markdown(f"**{key}: {result[key]}**")
                    scores.append(result[key])
        else:
            st.error("평가 결과가 예상한 형식이 아닙니다.")
            logger.error(f"Unexpected evaluation result format: {result}")
    else:
        st.warning("평가 결과가 아직 설정되지 않았습니다.")
        logger.warning("Evaluation result is not set.")





def main():
    if st.session_state.page == "select_topic":
        show_topic_selection()
    elif st.session_state.page == "topic_detail":
        if st.session_state.selected_topic:
            show_topic_detail()
        else:
            st.session_state.page = "select_topic"
    elif st.session_state.page == "chat":
        show_chat_interface()
    elif st.session_state.page == "eval":
        show_evaluation_page()  # 'eval' 페이지를 보여주는 함수 호출


# 디버깅을 위한 추가 기능
    if DEBUG_MODE:
        st.sidebar.title("Debugging Tools")
        if st.sidebar.button("Clear Session State"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            initialize_session_state()
            st.sidebar.success("Session state cleared!")
        
        if st.sidebar.button("Print Session State"):
            st.sidebar.json(st.session_state)
        
        if st.sidebar.button("Print Chat History"):
            st.sidebar.json(st.session_state.get('chat_history', []))
        
        if st.sidebar.button("Print Debate Bot State"):
            if 'debate_bot' in st.session_state:
                bot_state = {
                    "selected_char": st.session_state.debate_bot.selected_char,
                    "selected_topic": st.session_state.debate_bot.selected_topic,
                    "user_stance": st.session_state.debate_bot.user_stance,
                    "ai_stance": st.session_state.debate_bot.ai_stance
                }
                st.sidebar.json(bot_state)
            else:
                st.sidebar.warning("Debate Bot not initialized")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        st.error("An unexpected error occurred. Please check the logs for more information.")
        if DEBUG_MODE:
            st.error(f"Traceback: {traceback.format_exc()}")