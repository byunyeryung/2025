import streamlit as st
import random
from datetime import date

# 운세 목록
fortunes = [
    "🌞 오늘은 기분 좋은 일이 생길 거예요!",
    "🌧️ 조심하세요. 예상치 못한 일이 일어날 수 있어요.",
    "🍀 행운이 가득한 하루가 될 거예요!",
    "💼 일에서 좋은 기회가 찾아올지도 몰라요.",
    "❤️ 사랑하는 사람과 좋은 시간을 보내게 될 거예요.",
    "📚 오늘은 공부/일에 집중하기 좋은 날이에요.",
    "🧘 마음의 안정을 찾는 것이 중요해요.",
    "🚶‍♀️ 가벼운 산책이 오늘의 행운 포인트입니다!",
]

# Streamlit 앱
st.set_page_config(page_title="오늘의 운세", page_icon="🔮")
st.title("🔮 내일의 운세")

st.write("당신의 운세를 확인해보세요!")

# 사용자 입력
name = st.text_input("이름을 입력해주세요", "")

# 운세 보기 버튼
if st.button("운세 보기"):
    if name.strip() == "":
        st.warning("이름을 입력해주세요!")
    else:
        # 날짜 기반 seed로 하루에 한 번만 바뀌도록
        today = date.today().isoformat()
        seed_value = hash(name + today)
        random.seed(seed_value)
        fortune = random.choice(fortunes)

        st.success(f"{name}님의 오늘의 운세는:\n\n**{fortune}**")
