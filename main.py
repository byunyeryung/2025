import streamlit as st

# MBTI별 직업 추천 데이터
mbti_jobs = {
    "INTJ": ["전략 기획자", "데이터 과학자", "변호사", "교수"],
    "ENTP": ["기업가", "마케팅 전문가", "스타트업 창업자", "컨설턴트"],
    "INFJ": ["상담가", "작가", "심리학자", "사회운동가"],
    "ESFP": ["배우", "가수", "이벤트 플래너", "스포츠 코치"],
    # 필요시 계속 추가
}

st.title("MBTI 기반 진로 추천 웹앱")
st.write("당신의 MBTI를 선택하면 적합한 직업을 추천해드립니다!")

# MBTI 선택
mbti_list = list(mbti_jobs.keys())
user_mbti = st.selectbox("당신의 MBTI를 선택하세요:", mbti_list)

if user_mbti:
    st.subheader(f"✨ {user_mbti} 유형 추천 직업")
    jobs = mbti_jobs[user_mbti]
    for job in jobs:
        st.write(f"- {job}")

