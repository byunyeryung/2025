import streamlit as st
import pandas as pd
import altair as alt
import random

st.set_page_config(page_title="스마트 응급 자원 배분 앱", page_icon="🚑", layout="wide")

# -----------------------------
# 지역 데이터 (세분화)
# -----------------------------
regions = {
    "서울 강남": [37.4979, 127.0276],
    "서울 강북": [37.6100, 127.0293],
    "부산 서부": [35.1047, 128.9721],
    "부산 동부": [35.1796, 129.1356],
    "대구 북부": [35.9250, 128.5498],
    "대구 남부": [35.7988, 128.5830],
    "광주 동구": [35.1460, 126.9236],
    "광주 서구": [35.1527, 126.8906],
    "대전 유성": [36.3622, 127.3565],
    "대전 서구": [36.3510, 127.3845],
    "인천 중구": [37.4738, 126.6219],
    "인천 남동": [37.4475, 126.7314],
    "울산 북구": [35.5820, 129.3611],
    "울산 남구": [35.5384, 129.3114],
    "경기 수원": [37.2636, 127.0286],
    "경기 성남": [37.4200, 127.1265],
    "강원 춘천": [37.8813, 127.7302],
    "강원 강릉": [37.7519, 128.8761],
    "충북 청주": [36.6424, 127.4890],
    "충북 충주": [36.9910, 127.9250],
    "충남 천안": [36.8151, 127.1139],
    "충남 아산": [36.7899, 127.0019],
    "전북 전주": [35.8242, 127.1479],
    "전북 군산": [35.9677, 126.7362],
    "전남 목포": [34.8118, 126.3922],
    "전남 여수": [34.7604, 127.6622],
    "경북 포항": [36.0190, 129.3435],
    "경북 경주": [35.8562, 129.2247],
    "경남 창원": [35.2280, 128.6812],
    "경남 진주": [35.1802, 128.1076],
    "제주 제주시": [33.4996, 126.5312],
    "제주 서귀포": [33.2530, 126.5600]
}

# -----------------------------
# 더 많은 병원 데이터 자동 생성
# -----------------------------
hospital_list = []
for region, coords in regions.items():
    for i in range(1, 8):  # 각 지역에 7개 병원 생성
        hospital_list.append({
            "병원명": f"{region}병원{i}",
            "지역": region,
            "가용병상": random.randint(5, 50),
            "대기환자": random.randint(5, 80),
            "위도": coords[0] + random.uniform(-0.02, 0.02),
            "경도": coords[1] + random.uniform(-0.02, 0.02)
        })

hospital_data = pd.DataFrame(hospital_list)
hospital_data["가동률(%)"] = round((hospital_data["대기환자"] / (hospital_data["가용병상"]+1)) * 100, 1)

# -----------------------------
# 사이드바 입력
# -----------------------------
st.sidebar.header("🚨 응급 상황 설정")
region_choice = st.sidebar.selectbox("📍 현재 지역을 선택하세요", list(regions.keys()))
emergency_type = st.sidebar.selectbox("⚡ 응급 상황 유형", ["심정지", "화상", "골절", "호흡곤란", "출혈", "경련", "중독", "저체온증"])
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
# 응급 처치 가이드 (상세)
# -----------------------------
st.subheader("🩺 응급 처치 가이드")
if emergency_type == "심정지":
    st.info("1. 119 신고 후 즉시 CPR 시작 👉 30회 압박 + 2회 인공호흡 반복  2. AED 도착 시 즉시 사용  3. 전문 구조대 도착까지 계속 시행")
elif emergency_type == "화상":
    st.info("1. 흐르는 찬물에 최소 10~20분 냉각  2. 금속, 옷 등이 붙어있으면 억지로 제거하지 말 것  3. 수포 발생 시 터뜨리지 말고 멸균 거즈로 덮기  4. 얼굴, 호흡기 화상은 즉시 병원 이송")
elif emergency_type == "골절":
    st.info("1. 환자 움직이지 않게 고정  2. 부목이나 딱딱한 물체로 골절 부위 양쪽 고정  3. 부기 줄이기 위해 얼음찜질 가능  4. 출혈 동반 시 지혈 먼저 시행")
elif emergency_type == "호흡곤란":
    st.info("1. 편한 자세(앉은 자세) 유지  2. 조이는 옷 풀어주기  3. 산소 공급 가능 시 산소 제공  4. 의식 저하 시 기도 확보 및 심폐소생술 준비")
elif emergency_type == "출혈":
    st.info("1. 출혈 부위를 직접 압박  2. 출혈 심하면 지혈대 사용(사용 시간 기록)  3. 환자 체온 유지  4. 쇼크 예방 위해 다리 약간 올려주기")
elif emergency_type == "경련":
    st.info("1. 환자를 안전한 곳에 눕히고 머리 다치지 않게 보호  2. 억지로 몸을 누르지 말 것  3. 입에 물건 넣지 말 것  4. 경련이 5분 이상 지속되면 즉시 119 신고")
elif emergency_type == "중독":
    st.info("1. 의식 확인 후 기도·호흡·순환 상태 점검  2. 의식 있으면 물 조금 마시게 하기  3. 억지로 토하게 하지 말 것  4. 중독 원인 물질(약품, 음식) 함께 병원 전달")
else:  # 저체온증
    st.info("1. 젖은 옷 제거 후 담요로 덮어 체온 유지  2. 따뜻한 음료 제공(의식 있는 경우만)  3. 불필요한 움직임 최소화  4. 심한 경우 심폐소생술 준비")

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
