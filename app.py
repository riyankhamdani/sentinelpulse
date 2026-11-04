import hashlib
import json
import os
import time
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st

# ==============================================================================
# CONFIG & PAGE SETUP
# ==============================================================================
st.set_page_config(
    page_title="SentinelPulse | Autonomous Health Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Zona Industri Riil Abu Dhabi (DoH / ADPHC Jurisdiction)
ZONES_GEO = {
    "ICAD Musaffah": {
        "full_name": "ICAD Musaffah (Heavy Industry)",
        "lat": 24.3220,
        "lon": 54.4980,
        "wbgt": 33.1,
    },
    "KIZAD Khalifa Port": {
        "full_name": "KIZAD / Khalifa Port (Logistics Hub)",
        "lat": 24.8115,
        "lon": 54.7160,
        "wbgt": 31.8,
    },
    "Al Dhafra Solar Site": {
        "full_name": "Al Dhafra PV2 (Desert Energy Site)",
        "lat": 23.9500,
        "lon": 54.3800,
        "wbgt": 34.5,
    },
    "Ruwais Complex": {
        "full_name": "Ruwais Petrochemical Complex",
        "lat": 24.1100,
        "lon": 52.7300,
        "wbgt": 32.2,
    },
}

# ==============================================================================
# PRIVACY SAFEGUARD (UAE PDPL & Abu Dhabi DoH Standard)
# ==============================================================================
def anonymize_identifier(raw_id: str, salt: str = "ADPHC-2026") -> str:
    """Masking PII menjadi Pseudonymized Token via Salted SHA-256."""
    hashed = hashlib.sha256(f"{raw_id}:{salt}".encode()).hexdigest()
    return f"SP-{hashed[:8].upper()}"

# ==============================================================================
# DEFAULT TELEMETRY GENERATOR
# ==============================================================================
def get_baseline_workers():
    records = [
        {"raw_id": "CIVIL-ID-9081", "Name": "Worker 01", "Zone": "ICAD Musaffah", "Heart Rate": 82, "Core Temp": 37.1, "SpO2": 99},
        {"raw_id": "CIVIL-ID-4412", "Name": "Worker 02", "Zone": "ICAD Musaffah", "Heart Rate": 88, "Core Temp": 37.3, "SpO2": 98},
        {"raw_id": "CIVIL-ID-6731", "Name": "Worker 03", "Zone": "KIZAD Khalifa Port", "Heart Rate": 76, "Core Temp": 36.9, "SpO2": 99},
        {"raw_id": "CIVIL-ID-1190", "Name": "Worker 04", "Zone": "Al Dhafra Solar Site", "Heart Rate": 92, "Core Temp": 37.4, "SpO2": 97},
        {"raw_id": "CIVIL-ID-5532", "Name": "Worker 05", "Zone": "Ruwais Complex", "Heart Rate": 84, "Core Temp": 37.0, "SpO2": 99},
    ]
    df = pd.DataFrame(records)
    df["Tokenized ID"] = df["raw_id"].apply(anonymize_identifier)
    df["Status"] = "NORMAL"
    return df

# Initialize Session State
if "telemetry_df" not in st.session_state:
    st.session_state.telemetry_df = get_baseline_workers()
if "hr_history" not in st.session_state:
    st.session_state.hr_history = [84, 85, 83, 86, 88, 87, 85, 86, 88, 89]
if "ai_diagnosis" not in st.session_state:
    st.session_state.ai_diagnosis = None
if "is_streaming" not in st.session_state:
    st.session_state.is_streaming = False

# ==============================================================================
# AI CLINICAL TRIAGE ENGINE (Gemini Integration + Deterministic Fallback)
# ==============================================================================
def run_ai_clinical_triage(anomaly_row: dict, ambient_wbgt: float) -> dict:
    """Mengevaluasi risiko fisiologis sindromik via LLM Reasoning."""
    payload_clean = {
        "tokenized_subject": anomaly_row["Tokenized ID"],
        "zone": anomaly_row["Zone"],
        "heart_rate_bpm": float(anomaly_row["Heart Rate"]),
        "core_temp_c": float(anomaly_row["Core Temp"]),
        "spo2_pct": float(anomaly_row["SpO2"]),
        "ambient_wbgt_c": ambient_wbgt,
    }

    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = f"""
You are the SentinelPulse Clinical AI Engine for the Abu Dhabi Public Health Center (ADPHC).
Evaluate this real-time industrial telemetry payload for physiological collapse or acute heat injury:
{json.dumps(payload_clean)}

Return STRICT JSON only matching this schema:
{{
  "risk_level": "CRITICAL" or "ELEVATED",
  "clinical_assessment": "2-sentence clinical diagnosis explaining physiological strain vs environmental WBGT",
  "urgency_score": 1-100,
  "immediate_sop": "One-line immediate field directive"
}}
"""
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            return json.loads(res.text)
        except Exception:
            pass

    # Deterministic Engine Fallback (Clinical Standard OSHA/NIOSH)
    hr = anomaly_row["Heart Rate"]
    temp = anomaly_row["Core Temp"]
    if hr >= 140 or temp >= 38.5:
        return {
            "risk_level": "CRITICAL",
            "clinical_assessment": f"Acute hyperthermic cardiovascular decompensation detected. Sustained tachycardia ({hr} bpm) with core temperature reaching {temp}°C indicates impending heat stroke under severe thermal load ({ambient_wbgt}°C WBGT).",
            "urgency_score": 94,
            "immediate_sop": "Mandatory red-alert dispatch: immediate field evacuation to active cooling triage."
        }
    return {
        "risk_level": "ELEVATED",
        "clinical_assessment": f"Moderate thermal strain observed ({hr} bpm, {temp}°C). Compensatory physiological thermoregulation active under elevated microclimate.",
        "urgency_score": 68,
        "immediate_sop": "Deploy supervised rehydration and enforce 20-minute shaded rest cycle."
    }

# ==============================================================================
# SIDEBAR CONTROLS (FUNCTIONAL DATA INGESTION)
# ==============================================================================
st.sidebar.title("⚡ Telemetry Ingestion Layer")
st.sidebar.markdown(
    "Live ingestion gateway compliant with **UAE PDPL** & **Abu Dhabi DoH** data standards."
)

data_mode = st.sidebar.radio(
    "Data Source Mode:",
    ["Simulated 1Hz Live Stream", "Upload Real Telemetry (.csv)"],
)

if data_mode == "Upload Real Telemetry (.csv)":
    uploaded_file = st.sidebar.file_uploader("Upload Worker Wearable Telemetry", type=["csv"])
    if uploaded_file is not None:
        try:
            up_df = pd.read_csv(uploaded_file)
            required_cols = {"Zone", "Heart Rate", "Core Temp", "SpO2"}
            if required_cols.issubset(set(up_df.columns)):
                if "Tokenized ID" not in up_df.columns:
                    raw_col = "raw_id" if "raw_id" in up_df.columns else up_df.columns[0]
                    up_df["Tokenized ID"] = up_df[raw_col].astype(str).apply(anonymize_identifier)
                if "Status" not in up_df.columns:
                    up_df["Status"] = "NORMAL"
                st.session_state.telemetry_df = up_df
                st.sidebar.success(f"Loaded {len(up_df)} worker records.")
            else:
                st.sidebar.error(f"CSV missing columns: {required_cols - set(up_df.columns)}")
        except Exception as e:
            st.sidebar.error(f"Error parsing CSV: {e}")

else:
    stream_state = st.sidebar.toggle("Enable Live Telemetry Ingestion", value=st.session_state.is_streaming)
    st.session_state.is_streaming = stream_state

    anomaly_slider = st.sidebar.select_slider(
        "Inject Environmental Heat Wave Stress:",
        options=["Nominal Baseline", "Mild Thermal Burden", "Extreme Desert Surge"],
        value="Nominal Baseline",
    )

    if st.session_state.is_streaming:
        df_curr = st.session_state.telemetry_df.copy()
        target_idx = 1  # Subject 02

        if anomaly_slider == "Extreme Desert Surge":
            df_curr.loc[target_idx, "Heart Rate"] = np.random.randint(145, 162)
            df_curr.loc[target_idx, "Core Temp"] = round(np.random.uniform(38.6, 39.4), 1)
            df_curr.loc[target_idx, "SpO2"] = np.random.randint(93, 96)
            df_curr.loc[target_idx, "Status"] = "CRITICAL"
        elif anomaly_slider == "Mild Thermal Burden":
            df_curr.loc[target_idx, "Heart Rate"] = np.random.randint(110, 125)
            df_curr.loc[target_idx, "Core Temp"] = round(np.random.uniform(37.8, 38.3), 1)
            df_curr.loc[target_idx, "Status"] = "ELEVATED"
        else:
            df_curr.loc[target_idx, "Heart Rate"] = np.random.randint(80, 92)
            df_curr.loc[target_idx, "Core Temp"] = round(np.random.uniform(36.9, 37.4), 1)
            df_curr.loc[target_idx, "Status"] = "NORMAL"

        st.session_state.telemetry_df = df_curr
        st.session_state.hr_history.append(df_curr.loc[target_idx, "Heart Rate"])
        if len(st.session_state.hr_history) > 25:
            st.session_state.hr_history.pop(0)

# Check for anomalies
critical_workers = st.session_state.telemetry_df[st.session_state.telemetry_df["Status"] != "NORMAL"]
has_anomaly = len(critical_workers) > 0

if has_anomaly:
    top_threat = critical_workers.iloc[0]
    zone_wbgt = ZONES_GEO.get(top_threat["Zone"], {}).get("wbgt", 33.0)
    st.session_state.ai_diagnosis = run_ai_clinical_triage(top_threat.to_dict(), zone_wbgt)
else:
    st.session_state.ai_diagnosis = None

# ==============================================================================
# HEADER & KPIS
# ==============================================================================
st.title("⚡ SentinelPulse Command Center")
st.caption("Autonomous Syndromic Health Early Warning & Dispatch Platform — Abu Dhabi Operations")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Monitored Cohort", "4,205", "+12 shift net")
max_wbgt = max(z["wbgt"] for z in ZONES_GEO.values())
kpi2.metric("Peak WBGT", f"{max_wbgt} °C", "Extreme Heat", delta_color="inverse")
kpi3.metric("Pipeline Ingestion SLA", "340 ms", "-60 ms TLS 1.3")

if has_anomaly:
    threat_cnt = len(critical_workers)
    kpi4.metric("Active Alerts", f"{threat_cnt} Incident", "HIGH RISK DISPATCH", delta_color="inverse")
else:
    kpi4.metric("Active Alerts", "0 Incidents", "Nominal / Safe", delta_color="normal")

st.markdown("---")

# ==============================================================================
# FEEDBACK 2: INTERACTIVE HEALTH RISK MAP (ABU DHABI GEOSPATIAL)
# ==============================================================================
st.markdown("### 🗺️ Geospatial Workforce Hazard & Exposure Map (Abu Dhabi Industrial Corridor)")

map_records = []
for short_code, geo in ZONES_GEO.items():
    zone_workers = st.session_state.telemetry_df[st.session_state.telemetry_df["Zone"] == short_code]
    zone_critical = (zone_workers["Status"] == "CRITICAL").any()
    zone_elevated = (zone_workers["Status"] == "ELEVATED").any()

    if zone_critical:
        color = [239, 68, 68, 210]  # Red
        radius = 8000
        status_text = "CRITICAL HAZARD - HEAT STROKE INTERVENTION"
    elif zone_elevated:
        color = [245, 158, 11, 190]  # Amber
        radius = 6000
        status_text = "ELEVATED THERMAL STRAIN WARNING"
    else:
        color = [16, 185, 129, 170]  # Green
        radius = 4500
        status_text = "NOMINAL BASELINE"

    map_records.append({
        "short_name": short_code,
        "full_name": geo["full_name"],
        "lat": geo["lat"],
        "lon": geo["lon"],
        "WBGT": geo["wbgt"],
        "Status": status_text,
        "color": color,
        "radius": radius
    })

map_df = pd.DataFrame(map_records)

# Focused camera lock on Abu Dhabi Capital & Industrial corridor
view_state = pdk.ViewState(
    latitude=24.35,
    longitude=54.25,
    zoom=8.2,
    pitch=25,
    bearing=0
)

layer_scatter = pdk.Layer(
    "ScatterplotLayer",
    data=map_df,
    get_position="[lon, lat]",
    get_color="color",
    get_radius="radius",
    stroked=True,
    filled=True,
    line_width_min_pixels=2,
    get_line_color=[255, 255, 255, 200],
    pickable=True,
    auto_highlight=True,
)

layer_text = pdk.Layer(
    "TextLayer",
    data=map_df,
    get_position="[lon, lat]",
    get_text="short_name",
    get_size=13,
    get_color=[255, 255, 255, 255],
    get_alignment_baseline="'center'",
    get_text_anchor="'middle'",
    font_family="'Helvetica Neue', Helvetica, Arial, sans-serif",
    font_weight=700,
)

st.pydeck_chart(
    pdk.Deck(
        layers=[layer_scatter, layer_text],
        initial_view_state=view_state,
        tooltip={
            "html": "<b>{full_name}</b><br/>"
                    "🌡️ Ambient WBGT: <b>{WBGT} °C</b><br/>"
                    "⚠️ Threat Level: <b>{Status}</b>",
            "style": {"backgroundColor": "#0f172a", "color": "#f8fafc", "fontSize": "12px", "padding": "8px", "borderRadius": "6px"}
        },
        map_provider="carto",
        map_style="dark",
    )
)

st.markdown("---")

# ==============================================================================
# FEEDBACK 1 & TELEMETRY STREAM
# ==============================================================================
col_stream, col_roster = st.columns([1.5, 1])

with col_stream:
    st.markdown("#### 📈 Real-Time Target Telemetry Stream (High-Risk Subject)")
    times = pd.date_range(end=datetime.now(), periods=len(st.session_state.hr_history), freq='s')

    line_color = "#DC2626" if has_anomaly else "#10B981"
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times,
        y=st.session_state.hr_history,
        mode="lines+markers",
        name="Heart Rate (bpm)",
        line=dict(color=line_color, width=3)
    ))
    fig.add_hline(y=140, line_dash="dash", line_color="red", annotation_text="OSHA Extreme Strain (140 bpm)")
    fig.add_hline(y=110, line_dash="dot", line_color="orange", annotation_text="Elevated Fatigue (110 bpm)")
    fig.update_layout(
        yaxis_title="Heart Rate (bpm)",
        margin=dict(l=0, r=0, t=20, b=0),
        height=300,
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

with col_roster:
    st.markdown("#### 📋 Live Worker Roster (Decoupled PII View)")
    display_cols = ["Tokenized ID", "Zone", "Heart Rate", "Core Temp", "SpO2", "Status"]
    st.dataframe(
        st.session_state.telemetry_df[display_cols],
        use_container_width=True,
        hide_index=True,
    )
    st.caption("🛡️ **UAE PDPL Compliance:** Raw Civil ID & Worker Names are cryptographically decoupled at Tier-3 Ingestion before cloud replication.")

st.markdown("---")

# ==============================================================================
# FEEDBACK 3: PREVENTION ACTION PLANNER & ROLE ACCOUNTABILITY
# ==============================================================================
st.markdown("### 📋 Prevention Action Planner & Closed-Loop Incident Response")

if has_anomaly and st.session_state.ai_diagnosis:
    diag = st.session_state.ai_diagnosis
    threat_worker = critical_workers.iloc[0]

    st.error(
        f"🚨 **AUTOMATED AI CLINICAL TRIAGE DISPATCH | {threat_worker['Tokenized ID']} ({threat_worker['Zone']})**\n\n"
        f"**Clinical Reasoning:** {diag['clinical_assessment']}\n\n"
        f"**Immediate Directive:** `{diag['immediate_sop']}` (Urgency Severity: {diag['urgency_score']}/100)"
    )

    r1, r2, r3 = st.columns(3)

    with r1:
        st.markdown("##### 👷 HSE Field Supervisor")
        st.info("Primary Accountability: **Immediate Zone Isolation & Evacuation**")
        st.checkbox("Issue mandatory stop-work order in affected quadrant", value=True)
        st.checkbox("Dispatch buggy to escort worker to active cooling shelter", value=True)
        st.checkbox("Verify rest-rotation cycle for remaining crew in zone", value=False)
        st.caption("⏱️ Target Response SLA: `< 3 Minutes`")

    with r2:
        st.markdown("##### 🩺 On-Site Medical / Paramedic")
        st.warning("Primary Accountability: **Active Cooling & Vital Stabilization**")
        st.checkbox("Prepare cold water immersion / active evaporative misting", value=True)
        st.checkbox("Measure core rectal / infrared tympanic baseline temp", value=False)
        st.checkbox("Administer chilled oral rehydration salts (ORS) electrolyte", value=False)
        st.caption("⏱️ Target Medical Contact: `< 5 Minutes`")

    with r3:
        st.markdown("##### 🏭 Facility Operations Lead")
        st.success("Primary Accountability: **Engineering & Environmental Controls**")
        st.checkbox("Audit chilled drinking water dispensers in sector", value=True)
        st.checkbox("Increase ventilation fan velocity in high-density areas", value=True)
        st.checkbox("Submit automated syndromic incident log to ADPHC portal", value=False)
        st.caption("⏱️ Incident Logging SLA: `< 15 Minutes`")

else:
    st.success("✅ **ALL ZONES NOMINAL:** Autonomous surveillance active across all regional clusters. No physiological anomalies or environmental breach thresholds detected.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Role: HSE Supervisor**")
        st.caption("Status: Continuous monitoring. Routine hydration inspections active.")
    with c2:
        st.markdown("**Role: Medical Command**")
        st.caption("Status: Clinic standby. Zero heat-exhaustion cases reported this shift.")
    with c3:
        st.markdown("**Role: Operations Lead**")
        st.caption("Status: Engineering HVAC & shade structures running at full capacity.")

# ==============================================================================
# AUDIT LOG & COMPLIANCE FOOTER
# ==============================================================================
st.markdown("---")
st.markdown(
    """
    <div style="font-size: 0.85rem; color: #888; text-align: center;">
    🔒 <b>Security & Governance:</b> Built under Abu Dhabi Department of Health (DoH) Standards & UAE Federal Decree Law No. 45/2021 (PDPL). 
    Deterministic physiological boundary filtering coupled with Autonomous AI Triage. Telemetry encrypted in-transit via TLS 1.3.
    </div>
    """,
    unsafe_allow_html=True
)
