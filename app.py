import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="SentinelPulse Command Center", layout="wide", initial_sidebar_state="expanded")

def generate_worker_data():
    return pd.DataFrame({
        'Worker ID': [f'WRK-{i:03d}' for i in range(1, 6)],
        'Zone': ['Camp A', 'Camp A', 'Camp B', 'Camp C', 'Camp A'],
        'Heart Rate (bpm)': [82, 88, 76, 91, 84],
        'Skin Temp (°C)': [36.8, 37.1, 36.6, 37.2, 36.9],
        'Status': ['Normal', 'Normal', 'Normal', 'Normal', 'Normal']
    })

if 'data' not in st.session_state:
    st.session_state.data = generate_worker_data()
if 'alert_triggered' not in st.session_state:
    st.session_state.alert_triggered = False

st.title("⚡ SentinelPulse")
st.subheader("Regional Workforce Health Early Warning & Dispatch Center")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Active Workers Monitored", "4,205", "+12 shift net")
col2.metric("Ambient WBGT (Camp A)", "32.4 °C", "Extreme Heat", delta_color="inverse")
col3.metric("System Latency", "1.2 ms", "-0.3 ms")

if st.session_state.alert_triggered:
    col4.metric("Active Field Alerts", "1", "CRITICAL", delta_color="inverse")
else:
    col4.metric("Active Field Alerts", "0", "Nominal", delta_color="normal")

st.markdown("---")

st.sidebar.header("🛠️ Simulation Controls")
st.sidebar.markdown("Trigger an incoming physiological anomaly from wearable telemetry.")

if st.sidebar.button("🚨 Simulate Heat Stress Anomaly (WRK-002)"):
    st.session_state.alert_triggered = True
    st.session_state.data.loc[1, 'Heart Rate (bpm)'] = 152
    st.session_state.data.loc[1, 'Skin Temp (°C)'] = 38.9
    st.session_state.data.loc[1, 'Status'] = 'CRITICAL'

if st.sidebar.button("✅ Resolve Alert"):
    st.session_state.alert_triggered = False
    st.session_state.data = generate_worker_data()

if st.session_state.alert_triggered:
    st.error("⚠️ **CRITICAL DISPATCH TRIGGERED (Sub-2s SLA):** Worker WRK-002 (Camp A) breached physiological baselines: Sustained HR at 152 bpm with Skin Temp 38.9°C under 32.4°C WBGT. Immediate hydration and mandatory shade rest dispatched to Field Supervisor.")

col_chart, col_table = st.columns([2, 1])

with col_chart:
    st.markdown("#### 📈 Real-Time Vitals Stream (WRK-002)")
    times = pd.date_range(end=datetime.now(), periods=20, freq='s')
    
    if st.session_state.alert_triggered:
        hr_data = np.concatenate([np.random.randint(80, 95, 14), np.linspace(95, 152, 6)])
        line_color = '#DC2626'
    else:
        hr_data = np.random.randint(80, 92, 20)
        line_color = '#10B981'
        
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=hr_data, mode='lines+markers', name='Heart Rate', line=dict(color=line_color, width=3)))
    fig.add_hline(y=130, line_dash="dash", line_color="red", annotation_text="Safety Threshold (130 bpm)")
    fig.update_layout(yaxis_title="Heart Rate (bpm)", margin=dict(l=0, r=0, t=20, b=0), height=320)
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("#### 📋 Live Worker Roster")
    st.dataframe(
        st.session_state.data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn(
                "Status",
                help="Operational safety indicator",
            )
        }
    )
