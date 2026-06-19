import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# 1. 페이지 기본 설정 (다크 모드 유지)
st.set_page_config(
    page_title="조선소 통합 공정 관제 시스템 (Layout Reordered)",
    page_icon="🚢",
    layout="wide"
)

# 다크 모드 테마 적용을 위한 커스텀 CSS
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    [data-testid="stSidebar"] { background-color: #1e293b; border-right: 1px solid #334155; }
    [data-testid="stSidebar"] * { color: #f1f5f9 !important; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label { color: #cbd5e1 !important; }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; }
    [data-testid="stMetricDelta"] div { color: #ef4444 !important; }
    .stDataFrame, .stTable { border: 1px solid #334155; }
    .stDataFrame th, .stTable th { background-color: #111827; color: #38bdf8; }
    .stDataFrame td, .stTable td { color: #f1f5f9; }
    [data-testid="stTable"] .stMarkdown { color: #f1f5f9 !important; }
    [data-testid="stTable"] thead tr th div p { color: #38bdf8 !important; }
    [data-testid="stTable"] thead tr th { background-color: #111827 !important; }
    
    .ai-box {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #0284c7;
        color: #f1f5f9;
        margin-bottom: 20px;
    }
    .ai-box h5 { color: #38bdf8; margin-top: 0; }
    .ai-box ul { padding-left: 20px; }
    .ai-box li strong { color: #38bdf8; }
    .stMarkdown, .stCaption { color: #f1f5f9; }
    h1, h2, h3, h4, h5, h6 { color: #38bdf8 !important; }
    .plot-container { background-color: #1e293b; padding: 10px; border-radius: 10px; border: 1px solid #334155; }
    </style>
""", unsafe_allow_html=True)

# Matplotlib 다크 모드 폰트 및 스타일 설정
plt.rc('font', family='Malgun Gothic') 
plt.rcParams['axes.unicode_minus'] = False
plt.style.use('dark_background')

# ==========================================
# ⏱️ 1단계: 실시간 현재 시스템 시간 동적 바인딩
# ==========================================
current_now = datetime.now()
today_ref = current_now.date()
current_hour = current_now.hour

# ==========================================
# 📊 2단계: 실시간 연동용 마스터 가상 데이터 생성기
# ==========================================
@st.cache_data(ttl=60)
def generate_master_data(base_date):
    np.random.seed(42)
    n_rows = 5000
    
    start_date_pool = base_date - timedelta(days=45)
    delta_days = (base_date - start_date_pool).days
   
    random_days = np.random.randint(0, delta_days + 1, size=n_rows)
    date_list = [start_date_pool + timedelta(days=int(d)) for d in random_days]
    
    hour_list = np.random.randint(7, 20, size=n_rows)
    
    ships = np.random.choice(["LNG선", "컨테이너선", "벌크선", "VLCC"], size=n_rows, p=[0.3, 0.3, 0.2, 0.2])
    processes = np.random.choice(["용접", "도장", "조립"], size=n_rows, p=[0.4, 0.3, 0.3])
    
    managers_pool = {
        "용접": ["김OO", "최OO", "조OO"],
        "도장": ["박OO", "정OO", "윤OO"],
        "조립": ["이OO", "강OO", "장OO"]
    }
    managers = [np.random.choice(managers_pool[p]) for p in processes]
    statuses = np.random.choice(["진행중", "지연", "완료"], size=n_rows, p=[0.25, 0.15, 0.60])
    
    base_hours = {"용접": 4.2, "도장": 7.8, "조립": 6.5}
    hours = [base_hours[p] + np.random.normal(0, 1.2) for p in processes]
    hours = np.clip(hours, 1.0, 16.0)
    
    base_costs = {"용접": 150, "도장": 320, "조립": 580}
    material_costs = [base_costs[p] + int(np.random.normal(0, 70)) for p in processes]
    material_costs = np.clip(material_costs, 30, 1200)
    
    df_generated = pd.DataFrame({
        "작업ID": [f"TK-{i:04d}" for i in range(1, n_rows + 1)],
        "날짜": date_list,
        "시간": hour_list,
        "선박": ships,
        "공정": processes,
        "담당자": managers,
        "상태": statuses,
        "작업시간(시간)": np.round(hours, 1),
        "자재비(만원)": material_costs
    })
    return df_generated

df_master = generate_master_data(today_ref)


# ==========================================
# 📅 3단계: 사이드바 필터 및 실시간 날짜 슬라이싱 계산
# ==========================================
st.sidebar.image("C:\Streamlit실습\ship.png", width=400)
st.sidebar.title("⚓ 관제 필터 패널")

st.sidebar.subheader("📅 기간 선택")
period_option = st.sidebar.radio(
    "조회 기간을 선택하세요",
    ["오늘", "이번 주", "이번 달", "사용자 지정"]
)

if period_option == "오늘":
    start_dt, end_dt = today_ref, today_ref
elif period_option == "이번 주":
    start_dt = today_ref - timedelta(days=today_ref.weekday())  
    end_dt = start_dt + timedelta(days=6)
elif period_option == "이번 달":
    start_dt = today_ref.replace(day=1)  
    next_month = (start_dt.replace(day=28) + timedelta(days=4))
    end_dt = next_month - timedelta(days=next_month.day)  
elif period_option == "사용자 지정":
    date_range = st.sidebar.date_input("시작일 - 종료일", [today_ref - timedelta(days=7), today_ref])
    if len(date_range) == 2:
        start_dt, end_dt = date_range[0], date_range[1]
    else:
        start_dt, end_dt = date_range[0], date_range[0]

st.sidebar.subheader("🛠️ 공정 선택")
process_filter = st.sidebar.multiselect(
    "조회할 공정을 선택하세요",
    ["용접", "도장", "조립"],
    default=["용접", "도장", "조립"]
)

df_period = df_master[(df_master["날짜"] >= start_dt) & (df_master["날짜"] <= end_dt)]

if period_option == "오늘":
    df_period = df_period[df_period["시간"] <= current_hour]

df = df_period[df_period["공정"].isin(process_filter)]

st.sidebar.markdown("---")
if st.sidebar.button("🔄 즉시 리프레시 (동기화)"):
    st.rerun()


# ==========================================
# 🏢 헤더 영역
# ==========================================
col_title, col_logo = st.columns([3.5, 1.5])
with col_title:
    st.title("🚢 AI 기반 조선소 작업 공정 지연분석 시스템")
    st.caption("Smart Shipyard Manufacturing Execution System (MES) & Predictive Dashboard")
with col_logo:
    st.markdown(f"""
        <div style='text-align: right; padding-top: 10px;'>
            <span style='color: #10b981; font-weight: bold;'>● LIVE SYSTEM ACTIVE</span><br>
            <span style='color: #94a3b8; font-size: 13px;'>조회 시점: {current_now.strftime('%Y-%m-%d %H:%M:%S')}</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.image(r"C:\Streamlit실습\H-3245 Container Ship.png", caption="H-3245 Container Ship (실시간 데이터 동기화 모드)", use_container_width=True)
st.markdown("---")


# ==========================================
# 1. KPI 카드 연산
# ==========================================
st.subheader(f"📊 실시간 핵심 생산성 지표 (KPI) - [{period_option} 현황]")

total_tasks = len(df)
in_progress_tasks = len(df[df["상태"] == "진행중"])
completed_tasks = len(df[df["상태"] == "완료"])
delayed_tasks = len(df[df["상태"] == "지연"])
avg_time = df["작업시간(시간)"].mean() if total_tasks > 0 else 0.0
productivity_rate = int((completed_tasks / (completed_tasks + delayed_tasks + 0.1)) * 100) if total_tasks > 0 else 0
productivity_rate = min(max(productivity_rate, 45), 100)

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: st.metric(label="📊 총 작업 건수", value=f"{total_tasks:,} 건")
with k2: st.metric(label="⚡ 진행 중 작업", value=f"{in_progress_tasks:,} 건")
with k3: st.metric(label="✅ 완료 작업", value=f"{completed_tasks:,} 건")
with k4: st.metric(label="🚨 지연 작업", value=f"{delayed_tasks:,} 건", delta=f"{delayed_tasks}건 관제 필요", delta_color="inverse")
with k5: st.metric(label="⏱️ 평균 작업시간", value=f"{avg_time:.1f} 시간")
with k6: st.metric(label="📈 공정 생산성", value=f"{productivity_rate} %")
st.markdown("---")


# ==========================================
# 변경 상단: 2. 공정별 진행률 현황 및 4. 공정별 통계 분석 리포트
# ==========================================
col_prog, col_time = st.columns(2)

with col_prog:
    st.subheader("🔄 공정별 진행률 현황")
    if total_tasks > 0:
        for p in ["용접", "도장", "조립"]:
            if p in process_filter:
                df_p = df[df["공정"] == p]
                total_p = len(df_p)
                comp_p = len(df_p[df_p["상태"] == "완료"])
                rate_p = (comp_p / total_p) if total_p > 0 else 0.0
                st.write(f"**{p} 공정** : {int(rate_p*100)}%")
                st.progress(rate_p)
    else:
        st.info("선택된 조건에 작업 데이터가 존재하지 않습니다.")

with col_time:
    st.subheader("⏱️ 공정별 통계 분석 리포트")
    if not df.empty:
        df_stats_calc = df.groupby("공정")["작업시간(시간)"].agg(['mean', 'max', 'min', 'std']).reset_index()
        df_stats_calc.columns = ["공정", "평균 (h)", "최대 (h)", "최소 (h)", "표준편차 (σ)"]
        st.table(df_stats_calc.set_index("공정").round(2).fillna(0))
    else:
        st.write("데이터가 없습니다.")

st.markdown("---")


# ==========================================
# 중단: 생산 추이 · 공수 현황 · 자재비 분포 통합 대시보드 이미지
# ==========================================
st.subheader("📊 생산 추이 · 공수 현황 · 자재비 분포 통합 대시보드")

if not df.empty:
    fig_integrated, axes = plt.subplots(1, 3, figsize=(18, 5.2))
    fig_integrated.patch.set_facecolor('#1e293b')
    
    if period_option == "오늘":
        g_key = "시간"
        x_label_text = "시간 (시)"
        x_data = df.groupby("시간").size().index.astype(str) + "시"
    else:
        g_key = "날짜"
        x_label_text = "조회 일자"
        x_data = df.groupby("날짜").size().index.astype(str)

    # 1) 생산 추이
    df_only_completed = df[df["상태"] == "완료"]
    trend_data = df_only_completed.groupby(g_key).size()
    full_groups = df.groupby(g_key).size().index
    trend_data = trend_data.reindex(full_groups, fill_value=0)
    
    axes[0].plot(x_data, trend_data.values, marker='o', color='#38bdf8', linewidth=2.5, label="완료 건수")
    axes[0].set_title("① 각 날짜별(시간별) 생산 추이", color="#38bdf8", fontsize=12, pad=10)
    axes[0].set_xlabel(x_label_text, color="#94a3b8")
    axes[0].set_ylabel("작업 완료 건수 (건)", color="#94a3b8")
    axes[0].grid(True, linestyle=':', alpha=0.4, color='#334155')
    if period_option != "오늘": axes[0].tick_params(axis='x', rotation=45)

    # 2) 공수 현황
    manhour_data = df.groupby("공정")["작업시간(시간)"].sum().reset_index()
    sns.barplot(data=manhour_data, x="공정", y="작업시간(시간)", palette="GnBu_r", ax=axes[1])
    axes[1].set_title("② 실시간 누적 투입 공수 현황 (M/H)", color="#38bdf8", fontsize=12, pad=10)
    axes[1].set_xlabel("공정 구분", color="#94a3b8")
    axes[1].set_ylabel("총 투입 공수 (Hour)", color="#94a3b8")
    axes[1].grid(True, linestyle=':', alpha=0.4, color='#334155')

    # 3) 자재비 분포
    sns.boxplot(data=df, x="선박", y="자재비(만원)", palette="Purples", ax=axes[2], linewidth=1.5)
    axes[2].set_title("③ 선종별 자재비 투입 통계 분포", color="#38bdf8", fontsize=12, pad=10)
    axes[2].set_xlabel("선박 종류", color="#94a3b8")
    axes[2].set_ylabel("자재비 규모 (만원)", color="#94a3b8")
    axes[2].grid(True, linestyle=':', alpha=0.4, color='#334155')

    plt.tight_layout()
    st.pyplot(fig_integrated)
else:
    st.info("통합 대시보드를 렌더링하기 위한 데이터 셋이 존재하지 않습니다.")

st.markdown("---")


# ==========================================
# 변경 하단: 3. 공정별 지연 건수 및 6. 일별/시간별 생산성 추이 그래프
# ==========================================
col_delay, col_trend = st.columns(2)

with col_delay:
    st.subheader("🚨 공정별 지연 건수 (병목 구간)")
    if total_tasks > 0:
        df_delayed_only = df[df["상태"] == "지연"]
        delay_counts = df_delayed_only.groupby("공정").size().to_dict()
        for p in process_filter:
            if p not in delay_counts: delay_counts[p] = 0
                
        fig, ax = plt.subplots(figsize=(6, 3.2))
        sns.barplot(x=list(delay_counts.keys()), y=list(delay_counts.values()), palette="Reds_r", ax=ax)
        ax.set_ylabel("지연 건수 (건)")
        fig.patch.set_facecolor('#1e293b')
        st.pyplot(fig)
    else:
        st.info("지연 데이터가 없습니다.")

with col_trend:
    if period_option == "오늘":
        st.subheader("📈 금일 시간대별(Hourly) 생산성 추이")
        group_key = "시간"
        x_label = "조회 시간 (시)"
    else:
        st.subheader("📈 6. 일별(Daily) 생산성 및 지연율 추이")
        group_key = "날짜"
        x_label = "조회 일자"

    if not df_period.empty:
        df_trend_grp = df_period.groupby(group_key).apply(
            lambda x: pd.Series({
                "완료율": (len(x[x["상태"]=="완료"]) / len(x)) * 100 if len(x)>0 else 0,
                "지연율": (len(x[x["상태"]=="지연"]) / len(x)) * 100 if len(x)>0 else 0
            })
        ).reset_index().sort_values(group_key)
        
        fig2, ax2 = plt.subplots(figsize=(6, 3.2))
        
        if period_option == "오늘":
            x_axis_data = df_trend_grp["시간"].astype(str) + "시"
        else:
            x_axis_data = df_trend_grp["날짜"].astype(str)
            plt.xticks(rotation=45)
            
        ax2.plot(x_axis_data, df_trend_grp["완료율"], marker='o', label="완료율 (%)", color="#10b981", linewidth=2)
        ax2.plot(x_axis_data, df_trend_grp["지연율"], marker='s', label="지연율 (%)", color="#ef4444", linewidth=2)
        ax2.set_xlabel(x_label)
        ax2.set_ylabel("비율 (%)")
        ax2.legend()
        fig2.patch.set_facecolor('#1e293b')
        st.pyplot(fig2)
    else:
        st.write("추이 그래프를 표현할 데이터가 부족합니다.")

st.markdown("---")


# ==========================================
# 5. 실시간 작업 현황 테이블
# ==========================================
st.subheader("🔍 실시간 종합 작업 현황판")
search_query = st.text_input("🚢 검색창: 찾으시는 선박 종류 또는 담당자 이름을 입력하세요", "")

if search_query:
    df_filtered = df[df["선박"].str.contains(search_query) | df["담당자"].str.contains(search_query)]
else:
    df_filtered = df

st.dataframe(df_filtered.sort_values(by=["날짜", "시간"], ascending=False), use_container_width=True, hide_index=True)
st.markdown("---")


# ==========================================
# 7 & 10 & 8. AI 예측 결과 및 실시간 Alert 조건 자동화
# ==========================================
col_ai, col_alert_dock = st.columns(2)

welding_delay_rate = (len(df[(df["공정"]=="용접") & (df["상태"]=="지연")]) / len(df[df["공정"]=="용접"]) * 100) if len(df[df["공정"]=="용접"]) > 0 else 0
painting_delay_rate = (len(df[(df["공정"]=="도장") & (df["상태"]=="지연")]) / len(df[df["공정"]=="도장"]) * 100) if len(df[df["공정"]=="도장"]) > 0 else 0
assembly_delay_rate = (len(df[(df["공정"]=="조립") & (df["상태"]=="지연")]) / len(df[df["공정"]=="조립"]) * 100) if len(df[df["공정"]=="조립"]) > 0 else 0

with col_ai:
    st.subheader("🤖 AI 지능형 공정 예측 결과")
    rates = {"용접": welding_delay_rate, "도장": painting_delay_rate, "조립": assembly_delay_rate}
    max_risk_process = max(rates, key=rates.get) if total_tasks > 0 else "N/A"
    ai_prob = min(max(int(rates.get(max_risk_process, 0) * 3.8), 15), 95) if total_tasks > 0 else 0

    st.markdown(f"""
    <div class="ai-box">
        <h5>🛡️ AI 실시간 연동 분석 요약</h5>
        <ul>
            <li><strong>지정 기간 내 집중 분석 대상:</strong> {max_risk_process} 공정 리스크 누적</li>
            <li><strong>예상 지연 리스크 지수:</strong> <span style='color: #ef4444; font-weight: bold;'>{ai_prob}%</span></li>
            <li><strong>AI 가이드 완료 예측일:</strong> {(today_ref + timedelta(days=5)).strftime('%Y-%m-%d')}</li>
            <li><strong>정체 원인:</strong> 선택 기간 내 관측된 공기 초과 이력 및 누적 로드 연동 연산 결과</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col_alert_dock:
    st.subheader("⚠️ 실시간 병목 공정 조건 기반 알림")
    alert_triggered = False
    
    if painting_delay_rate > 5:
        st.warning(f"⚠️ **[도장 공정 경보]** 현재 지연율 {painting_delay_rate:.1f}% 기록 중! 대기 정체 현상이 심화되고 있습니다.")
        alert_triggered = True
    if welding_delay_rate > 5:
        st.error(f"🚨 **[용접 공정 위험]** 현재 지연율 {welding_delay_rate:.1f}% 초과! 자재 배치 시급.")
        alert_triggered = True
        
    if not alert_triggered:
        st.success("✅ **[안전]** 선택 기간 내 지연 현황이 경고 기준치 미만으로 안전하게 통제되고 있습니다.")

    st.markdown("---")
    
    st.subheader("📍 작업장(블록) 야드 배치 구조")
    with st.expander("🏗️ 실시간 도크(Dock)별 선박 블록 매핑 구조 보기"):
        dock1_status = "🟥 지연 관리 구간" if delayed_tasks > 5 else "🟩 정상 순항 중"
        st.markdown(f"""
        * **⚓ 도크 1 (Dock 1)** [{dock1_status}]
           * ├─ 🟥 **블록 A** (용접 공정 진행 중 / 현재 진척률 연동)
           * ├─ 🟨 **블록 B** (도장 공정 대기 / 분석 트리거 작동)
           * └─ 🟩 **블록 C** (조립 완료 단계 탑재 준비)
        * **⚓ 도크 2 (Dock 2)**
           * ├─ 🟩 **블록 D** (구조재 안착 완료)
           * └─ 🟩 **블록 E** (선각 절단 공정 진행 중)
        """, unsafe_allow_html=True)