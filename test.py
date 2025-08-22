# app.py
# -----------------------------------------------------------
# 🚑 스마트 응급 자원 배분 앱 (보건 + 경영 융합)
# - 응급 처치 가이드 (보건)
# - 인근 병원 자원 가시화 & 추천 (경영/자원 배분)
# - 발표/데모용 더미 데이터 내장 (외부 API 불필요)
# -----------------------------------------------------------

import time
from math import radians, sin, cos, sqrt, atan2
from io import StringIO

import pandas as pd
import streamlit as st
import numpy as np
import altair as alt

# ----------------------------
# 기본 설정 & 사이드바
# ----------------------------
st.set_page_config(page_title="스마트 응급 자원 배분", page_icon="🚑", layout="wide")

# 스타일 약간 정돈
st.markdown(
    """
    <style>
    .big-title {font-size: 2rem; font-weight: 800;}
    .subtle {color:#666;}
    .badge {display:inline-block; padding:2px 8px; border-radius:999px; background:#f1f5f9; margin-right:6px; font-size:0.8rem}
    .pill-red{background:#fee2e2}
    .pill-green{background:#dcfce7}
    .pill-yellow{background:#fef9c3}
    .pill-blue{background:#e0f2fe}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ 설정")
    st.caption("데모용 더미 데이터가 포함되어 있습니다.")
    st.markdown("---")
    st.subheader("📍 현재 위치 (위도/경도)")
    lat = st.number_input("위도", value=37.5665, format="%.6f")  # 서울시청 근처
    lon = st.number_input("경도", value=126.9780, format="%.6f")

    st.subheader("🚨 사고 정보")
    emergency = st.selectbox(
        "응급 유형",
        [
            "심정지(CPR)",
            "기도막힘(성인)",
            "기도막힘(영유아)",
            "심한 출혈",
            "화상",
            "골절 의심",
            "쇼크 의심",
            "뇌졸중 의심",
            "심근경색(심장마비) 의심",
        ],
    )

    age = st.slider("환자 연령", 0, 100, 35)
    conscious = st.selectbox("의식 여부", ["의식 있음", "의식 없음"]) 
    breathing = st.selectbox("호흡 여부", ["정상", "비정상/무호흡"]) 

    st.subheader("🚑 이송 수단")
    transport = st.radio("이송 방식", ["구급차 호출", "자가/동승 이송"], index=0)

    st.subheader("🎯 추천 기준 가중치")
    w_wait = st.slider("대기시간 가중치", 0.0, 1.0, 0.6, 0.05)
    w_distance = st.slider("거리 가중치", 0.0, 1.0, 0.3, 0.05)
    w_trauma = st.slider("권역외상센터 가중치(가산)", 0.0, 1.0, 0.1, 0.05)

# ----------------------------
# 데이터(더미): 병원 자원 현황
# ----------------------------
HOSPITAL_CSV = """
name,lat,lon,er_capacity,er_occupied,has_trauma,ambulances_available
서울종합병원,37.5640,126.9750,40,32,1,2
한강의료센터,37.5345,126.9940,55,50,0,1
강북응급의료원,37.6120,127.0080,30,22,0,1
남산응급센터,37.5502,126.9900,20,18,0,0
광진권역외상센터,37.5390,127.0820,70,60,1,3
마포시민병원,37.5530,126.9100,25,12,0,1
서초메디컬,37.4837,127.0324,35,29,0,1
송파응급케어,37.5146,127.1054,45,42,0,2
노원중앙병원,37.6542,127.0565,28,20,0,1
영등포응급센터,37.5172,126.9076,38,35,0,1
"""

def load_hospitals(csv_text: str) -> pd.DataFrame:
    df = pd.read_csv(StringIO(csv_text))
    df["er_utilization"] = (df["er_occupied"] / df["er_capacity"]).clip(0, 1)
    return df

hosp_df = load_hospitals(HOSPITAL_CSV)

# ----------------------------
# 유틸: 거리 계산 (하버사인)
# ----------------------------

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# ----------------------------
# 비즈니스 로직: 추정 대기시간/점수
# ----------------------------

def estimate_wait_minutes(row, transport_mode: str):
    # 기본 대기시간 모델(데모용 간단식)
    base = 15  # 분
    util_factor = 1 + 2.5 * row["er_utilization"]  # 혼잡할수록 늘어남
    amb_bonus = -5 if (transport_mode == "구급차 호출" and row["ambulances_available"] > 0) else 0
    return max(3, int(base * util_factor + amb_bonus))


def compute_scores(df: pd.DataFrame, lat: float, lon: float, transport_mode: str, emergency: str,
                   w_wait: float, w_distance: float, w_trauma: float) -> pd.DataFrame:
    tmp = df.copy()
    tmp["distance_km"] = tmp.apply(lambda r: haversine_km(lat, lon, r["lat"], r["lon"]), axis=1)
    tmp["est_wait_min"] = tmp.apply(lambda r: estimate_wait_minutes(r, transport_mode), axis=1)

    # 정규화
    for col in ["distance_km", "est_wait_min"]:
        if tmp[col].max() - tmp[col].min() > 0:
            tmp[col+"_norm"] = (tmp[col] - tmp[col].min()) / (tmp[col].max() - tmp[col].min())
        else:
            tmp[col+"_norm"] = 0.0

    # 응급 유형이 외상/심정지 계열이면 외상센터 가산
    trauma_bonus = np.where(tmp["has_trauma"] == 1, 1.0, 0.0)
    # 점수는 낮을수록 좋게: 대기/거리(가중 최소화) - 외상센터 가산(감점)
    tmp["score"] = (
        w_wait * tmp["est_wait_min_norm"] +
        w_distance * tmp["distance_km_norm"] -
        w_trauma * trauma_bonus
    )

    # 긴급도 색상 태그
    def tag(row):
        u = row["er_utilization"]
        if u >= 0.85:
            return "🔴 매우 혼잡"
        elif u >= 0.7:
            return "🟠 혼잡"
        elif u >= 0.5:
            return "🟡 보통"
        else:
            return "🟢 여유"
    tmp["혼잡도"] = tmp.apply(tag, axis=1)

    # 권장 병원 플래그
    tmp = tmp.sort_values(["score", "est_wait_min", "distance_km"]).reset_index(drop=True)
    tmp["추천"] = ["✅ 추천"] + [""] * (len(tmp) - 1)
    return tmp

# ----------------------------
# 응급 가이드 (요약 스텝)
# ----------------------------
GUIDES = {
    "심정지(CPR)": {
        "주의": [
            "본 앱은 교육용입니다. 즉시 119 신고하세요.",
            "AED가 보이면 즉시 가져오세요.",
        ],
        "단계": [
            "반응 확인(어깨 두드리며 큰 소리로 말하기)",
            "호흡 확인: 비정상/무호흡이면 즉시 119 신고 및 CPR 시작",
            "흉부압박 30회(분당 100~120회, 깊이 5~6cm)",
            "인공호흡 2회(가능할 때만). AED 도착 즉시 패드 부착 지시 따르기",
            "2분마다 호흡/맥박 재평가"
        ],
        "금지": ["의식/정상호흡이 확인되면 흉부압박을 하지 않습니다."]
    },
    "기도막힘(성인)": {
        "주의": [
            "기침 가능하면 기침을 지속하도록 격려하고 지켜봅니다.",
            "기침 불가/숨 못 쉬면 하임리히법 시행 및 즉시 119 신고",
        ],
        "단계": [
            "의식 있음: 복부 밀어올리기(하임리히) 반복",
            "의식 소실: 바로 CPR 시작, 입안 이물질 보이면 제거",
        ],
        "금지": ["등 두드리기와 복부 밀기를 동시에 하지 않습니다."]
    },
    "기도막힘(영유아)": {
        "주의": ["강한 복부 밀기는 영아에게 금지. 등 타격+가슴 압박 병행"],
        "단계": [
            "등 타격 5회 → 가슴 압박 5회 반복",
            "의식 소실 시 CPR 진행"
        ],
        "금지": ["영아에게 복부 밀어올리기 금지"]
    },
    "심한 출혈": {
        "주의": ["직접 압박이 최우선. 출혈 계속되면 지혈대 고려(사지)"],
        "단계": [
            "상처 부위를 깨끗한 천/붕대로 강하게 압박",
            "가능하면 환부 올리기",
            "지혈대 사용 시 시간 기록",
        ],
        "금지": ["출혈 부위에 무분별한 탐침/세척 금지"]
    },
    "화상": {
        "주의": ["20분 이내 미지근한 흐르는 물로 20분 이상 냉각"],
        "단계": [
            "금속/의복이 달라붙었으면 억지로 떼지 않기",
            "깨끗한 거즈로 느슨히 덮기",
        ],
        "금지": ["얼음 직접 적용 금지, 연고/치약 바르지 않기"]
    },
    "골절 의심": {
        "주의": ["부목으로 고정, 불필요한 움직임 최소화"],
        "단계": ["가벼운 쿠션/부목으로 관절 포함 고정", "냉찜질(얼음은 천으로 감싸서)"],
        "금지": ["돌출된 뼈 억지로 밀어 넣지 않기"]
    },
    "쇼크 의심": {
        "주의": ["119 신고, 다리 20~30cm 올리기(머리/척추 외상 의심 시 제외)"],
        "단계": ["보온 유지", "불필요한 움직임 최소화"],
        "금지": ["음식/물 섭취 금지"]
    },
    "뇌졸중 의심": {
        "주의": ["FAST 확인(안면/팔/말하기), 즉시 119"],
        "단계": ["증상 시작 시간 기록", "머리 과도한 굴곡/회전 피하기"],
        "금지": ["음식/물/약 임의 복용 금지"]
    },
    "심근경색(심장마비) 의심": {
        "주의": ["가슴 통증 10분↑ 지속/식은땀/구토 동반 시 즉시 119"],
        "단계": ["가능하면 휴식/편한 자세", "의식 소실 시 CPR 준비"],
        "금지": ["무리한 이동/운전 금지"]
    },
}

# ----------------------------
# 간이 Triage (교육용)
# ----------------------------

def triage_level(conscious: str, breathing: str, emergency: str):
    # 단순화된 교육용 로직
    if emergency == "심정지(CPR)" or breathing == "비정상/무호흡" or conscious == "의식 없음":
        return "🔴 최고 긴급(즉시)"
    if emergency in ["심한 출혈", "뇌졸중 의심", "심근경색(심장마비) 의심"]:
        return "🟠 고긴급"
    return "🟡 중간"


# ----------------------------
# 레이아웃
# ----------------------------
st.markdown('<div class="big-title">🚑 스마트 응급 자원 배분: 보건 × 경영</div>', unsafe_allow_html=True)
st.caption("교육/발표용 데모 • 실제 진료는 119 및 의료진 지시에 따르세요")

colA, colB = st.columns([1.1, 1])

with colA:
    st.subheader("1) 응급 처치 가이드")
    guide = GUIDES.get(emergency, {})

    if guide:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**⚠️ 주의사항**")
            for x in guide["주의"]:
                st.markdown(f"- {x}")
        with c2:
            st.markdown("**🪜 단계**")
            for i, x in enumerate(guide["단계"], 1):
                st.markdown(f"{i}. {x}")
        with c3:
            st.markdown("**⛔ 금지**")
            for x in guide["금지"]:
                st.markdown(f"- {x}")

        # CPR 전용: 2분 타이머(선택)
        if emergency == "심정지(CPR)":
            st.markdown("---")
            st.markdown("**⏱ CPR 2분 사이클 타이머 (데모용)**")
            if st.button("타이머 시작"):
                ph = st.empty()
                bar = st.progress(0)
                for sec in range(120):
                    bar.progress(int((sec+1)/120*100))
                    ph.info(f"경과: {sec+1}초 • 압박 100~120회/분 유지 • 2분마다 재평가")
                    time.sleep(0.05)  # 발표용으로 빠르게(실제 0.05초 = 1초 대용)
                ph.success("2분 경과! 호흡/맥박 재평가 후 계속 진행")

    st.markdown("---")
    st.subheader("2) 인근 병원 자원 & 추천 (경영 관점)")

    scored = compute_scores(
        hosp_df, lat, lon, transport, emergency, w_wait, w_distance, w_trauma
    )

    # 추천 요약 카드
    top = scored.iloc[0]
    st.markdown(
        f"**✅ 추천 병원: {top['name']}**  ")
    st.markdown(
        f"- 예상 대기: **{int(top['est_wait_min'])}분**  • 거리: **{top['distance_km']:.1f}km**  • 혼잡도: **{top['혼잡도']}**  "
    )

    # 표 (가독성 위해 간단 정리)
    view_cols = [
        "추천", "name", "혼잡도", "est_wait_min", "distance_km", "er_capacity", "er_occupied", "has_trauma", "ambulances_available",
    ]
    show = scored[view_cols].rename(columns={
        "name": "병원명",
        "est_wait_min": "예상대기(분)",
        "distance_km": "거리(km)",
        "er_capacity": "응급실 정원",
        "er_occupied": "현재 점유",
        "has_trauma": "외상센터",
        "ambulances_available": "가용 구급차",
    })

    # 스타일링
    def highlight_recommend(row):
        if row["추천"] == "✅ 추천":
            return ["background-color: #ecfeff"] * len(row)
        return [""] * len(row)

    st.dataframe(
        show.style.apply(highlight_recommend, axis=1).format({"거리(km)": "{:.1f}"}),
        use_container_width=True,
        height=360,
    )

    # 막대 차트: 대기시간 비교
    st.markdown("**병원별 예상 대기시간 비교**")
    chart_data = scored[["name", "est_wait_min", "has_trauma"]]
    bar = (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X("name", sort="-y", title="병원"),
            y=alt.Y("est_wait_min", title="예상 대기(분)"),
            tooltip=["name", "est_wait_min", alt.Tooltip("has_trauma", title="외상센터")],
        )
        .properties(height=260)
    )
    st.altair_chart(bar, use_container_width=True)

with colB:
    st.subheader("3) 현장 의사결정 요약")

    tri = triage_level(conscious, breathing, emergency)
    st.markdown(f"**긴급도 판단:** {tri}")

    bullet = [
        "119 신고 및 위치 공유는 가장 먼저!",
        "가능하면 **구급차 호출** 선택 (전문처치/AED/의료기관 연결)",
        "병원 선택 시: **대기시간 + 거리 + 전문성(외상센터)**를 함께 고려",
        "환자의 안전이 최우선. 자가이송은 위험할 수 있음",
    ]
    for b in bullet:
        st.markdown(f"- {b}")

    # 지도 표시
    st.markdown("---")
    st.markdown("**인근 병원 지도**")
    map_df = scored[["lat", "lon"]].copy()
    st.map(map_df, zoom=11)

    # 추가 지표 카드
    st.markdown("---")
    st.markdown("**지표 요약(경영 관점)**")
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        avg_util = scored["er_utilization"].mean()
        st.metric("평균 응급실 가동률", f"{avg_util*100:.0f}%")
    with kpi2:
        st.metric("평균 예상 대기", f"{int(scored['est_wait_min'].mean())}분")
    with kpi3:
        st.metric("외상센터 수", f"{int(scored['has_trauma'].sum())}개")

# ----------------------------
# 푸터/면책
# ----------------------------
st.markdown("---")
st.caption("ⓘ 본 앱은 교육/발표용 데모입니다. 실제 응급상황에서는 즉시 119에 신고하고, 의료진의 지시에 따르세요.")

