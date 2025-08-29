import streamlit as st
import random

# 페이지 설정
st.set_page_config(page_title="랜덤 숫자 뽑기", page_icon="🎲")

# 제목
st.title("🎲 1부터 50까지 랜덤 숫자 뽑기")

# 설명
st.write("아래 버튼을 클릭하면 1부터 50 사이의 숫자 중 하나가 랜덤으로 선택됩니다.")

# 버튼 클릭 시 숫자 생성
if st.button("숫자 뽑기"):
    number = random.randint(1, 50)
    st.success(f"✨ 선택된 숫자는 **{number}** 입니다!")
