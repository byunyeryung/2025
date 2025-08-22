import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="스마트 응급 자원 배분 앱", page_icon="🚑", layout="wide")

# -----------------------------
# 병원 데이터 (샘플)
# -----------------------------
regions = {
    "서울": [37.5665, 126.9780],
    "부산": [35.1796, 129.0756],
    "대구": [35.8714, 128.6014],
    "광주": [35.1595, 126.8526],
    "대전": [36.3504, 127.3845],
    "인천": [37.4563, 126.7052]
}

hospital_data = pd.DataFrame({
    "병원명": ["서울대병원", "부산의료원", "대구병원", "광주종합병원", "대전중앙병원", "인천길병원"],
    "지역": ["서울", "부산", "대구", "광주", "대전", "인천"],
    "가용병상": [12, 5, 8, 15, 7, 9],
    "대기환자": [30, 22, 18, 40, 25, 20],
    "위도": [37.5796, 35.2000, 35.8700, 35.1600, 36.3500, 37.4600],
    "경도": [126.9770, 129.0800, 128.6000, 126.8500, 127.3850, 126.7050]
})

hospital_data["가동률(%)"] = round((hospital_data["대기환자"] / (hospital_data["가용병상"]+1)) * 100, 1)

# -----------------------------
# 사이드바 입력
# -----------------------------
st.sidebar.header("🚨 응급 상황 설정")
region_choice = st.sidebar.selectbox("📍 현재 지역을 선택하세요", list(regions.keys()))
emergency_type = st.sidebar.selectbox("⚡ 응급 상황 유형", ["심정지", "화상", "골절", "호흡곤란", "출혈"])

criteria = st.sidebar.radio("🏥 병원 추천 기준", ["대기시간 짧음", "가용병상 많음"])

# -----------------------------
# 메인 화면
# -----------------------------
st.title("🚑 스마트 응급 자원 배분 앱")
st.markdown("""
이 앱은 **응급 처치 가이드**와 **병원 자원 상황**을 바탕으로, 
효율적인 응급 자원 배분을 돕습니다.
""")

# -----------------------------
# 응급 처치 가이드
# -----------------------------
st.subheader("🩺 응급 처치 가이드")
if emergency_type == "심정지":
    st.info("1. 119에 신고 📞  2. 즉시 심폐소생술(CPR) 시행  3. 자동심장충격기(AED) 사용")
elif emergency_type == "화상":
    st.info("1. 흐르는 찬물에 10분 이상 세척 💧  2. 물집 터뜨리지 말 것  3. 멸균 거즈로 덮기")
elif emergency_type == "골절":
    st.info("1. 환자 움직이지 않게 고정 🦴  2. 부목 이용  3. 즉시 병원 이송")
elif emergency_type == "호흡곤란":
    st.info("1. 환자 편한 자세 유지 😮‍💨  2. 조이는 옷 풀기  3. 신속히 의료 지원 요청")
else:
    st.info("1. 출혈 부위 압박 🩸  2. 심하면 지혈대 사용  3. 가능한 빨리 병원 이송")

# -----------------------------
# 병원 추천 & 시각화
# -----------------------------
st.subheader("🏥 인근 병원 상황")
region_hospitals = hospital_data[hospital_data["지역"] == region_choice]

if not region_hospitals.empty:
    if criteria == "대기시간 짧음":
        best_hospital = region_hospitals.sort_values("대기환자").iloc[0]
    else:
        best_hospital = region_hospitals.sort_values("가용병상", ascending=False).iloc[0]

    st.success(f"추천 병원: **{best_hospital['병원명']}** 🏥  ")

    st.write("📊 선택한 지역의 병원 데이터")
    st.dataframe(region_hospitals, use_container_width=True)

    chart = alt.Chart(region_hospitals).mark_bar().encode(
        x="병원명",
        y="대기환자",
        color="병원명"
    )
    st.altair_chart(chart, use_container_width=True)

    # 지도 표시
    st.subheader("🗺️ 지도에서 병원 위치 보기")
    st.map(region_hospitals.rename(columns={"위도": "lat", "경도": "lon"}))
else:
    st.warning("선택한 지역에 등록된 병원이 없습니다.")

# -----------------------------
# 요약
# -----------------------------
st.subheader("📌 요약")
st.write(f"현재 위치: **{region_choice}**  | 응급 유형: **{emergency_type}**  | 기준: **{criteria}**")
