import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="스마트 응급 자원 배분 앱", layout="wide")

# 제목
st.title("🚑 스마트 응급 자원 배분 앱")
st.markdown("### 보건 × 경영 융합 프로젝트")

# 지역 선택
regions = [
    "서울 강남", "서울 강북", "부산 서부", "부산 동부",
    "대구 남구", "대구 북구", "인천 연수구", "인천 부평구",
    "광주 동구", "광주 서구", "광주 남구", "광주 북구", "광주 광산구",
    "대전 유성구", "울산 중구", "세종시",
    "경기 수원", "경기 성남", "강원 춘천", "충북 청주", "충남 천안",
    "전북 전주", "전남 목포", "경북 포항", "경남 창원", "제주 제주시"
]

with st.sidebar:
    st.header("⚙️ 설정")
    region = st.selectbox("지역을 선택하세요", regions)
    emergency_type = st.selectbox(
        "응급 상황을 선택하세요",
        ["심정지", "출혈", "골절", "화상", "호흡곤란", "저체온증", "중독", "경련"]
    )
    priority = st.radio("추천 기준", ["대기시간", "가용병상"])

# 데이터 생성 함수
def generate_hospital_data(region, n=7):
    np.random.seed(len(region))
    return pd.DataFrame({
        "병원명": [f"{region} 병원 {i+1}" for i in range(n)],
        "대기환자": np.random.randint(0, 50, n),
        "가용병상": np.random.randint(0, 20, n),
        "위도": np.random.uniform(35.0, 37.5, n),
        "경도": np.random.uniform(126.5, 129.5, n)
    })

hospital_data = generate_hospital_data(region)

# 응급 처치 가이드
treatment_guide = {
    "심정지": "즉시 심폐소생술(CPR)을 시행하고 자동심장충격기(AED) 사용",
    "출혈": "출혈 부위를 압박하여 지혈하고 필요시 지혈대 사용",
    "골절": "부목으로 고정 후 환자를 움직이지 않게 안정",
    "화상": "상처 부위를 10분 이상 흐르는 물에 식히고 물집은 터뜨리지 않음",
    "호흡곤란": "환자를 편하게 앉히고 기도 확보, 필요시 인공호흡 준비",
    "저체온증": "젖은 옷을 벗기고 담요로 감싸 체온 유지",
    "중독": "원인 물질 확인 후, 구토 유발 금지. 즉시 의료기관 이송",
    "경련": "환자를 안전한 곳으로 옮기고 머리를 보호, 억지로 움직이지 않음"
}

# 추천 병원 선정
if priority == "대기시간":
    recommended = hospital_data.sort_values("대기환자").iloc[0]
else:
    recommended = hospital_data.sort_values("가용병상", ascending=False).iloc[0]

# 탭 UI
info_tab, hospital_tab, map_tab = st.tabs(["🩺 응급 처치 가이드", "🏥 병원 현황", "🗺️ 지도 보기"])

with info_tab:
    st.subheader("응급 처치 가이드")
    st.info(treatment_guide[emergency_type])

with hospital_tab:
    st.subheader(f"{region} 병원 현황")
    st.dataframe(hospital_data, use_container_width=True)

    chart = alt.Chart(hospital_data).mark_bar().encode(
        x='병원명',
        y='대기환자',
        tooltip=['병원명','대기환자','가용병상']
    ).properties(title="대기 환자 수 현황")
    st.altair_chart(chart, use_container_width=True)

    st.success(f"✅ 추천 병원: {recommended['병원명']} | 대기환자: {recommended['대기환자']}명 | 가용병상: {recommended['가용병상']}개")

with map_tab:
    st.subheader("병원 위치 지도")
    import pydeck as pdk

    layer = pdk.Layer(
        'ScatterplotLayer',
        data=hospital_data,
        get_position='[경도, 위도]',
        get_radius=200,
        get_fill_color=[0, 0, 255, 160],
        pickable=True
    )

    # 추천 병원 강조
    highlight = pdk.Layer(
        'ScatterplotLayer',
        data=pd.DataFrame([recommended]),
        get_position='[경도, 위도]',
        get_radius=400,
        get_fill_color=[255, 0, 0, 200],
        pickable=True
    )

    view_state = pdk.ViewState(latitude=hospital_data["위도"].mean(), longitude=hospital_data["경도"].mean(), zoom=10)
    st.pydeck_chart(pdk.Deck(layers=[layer, highlight], initial_view_state=view_state))
