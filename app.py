import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="SentinelPulse Command Center", layout="wide", initial_sidebar_state="expanded")

# --- MOCKUP DATA GENERATOR ---
def generate_worker_data():
    return pd.DataFrame({
        'Worker ID': [f'WRK-{i:03d}' for i in range(1, 6)],
        'Zone': ['Camp A', 'Camp A', 'Camp B', 'Camp C', 'Camp A'],
        'Heart Rate (bpm)': np.random.randint(70, 110, 5),
        'Skin Temp (°C)': np.round(np.random.uniform(36.5, 37.8, 5), 1),
        'Status': ['Normal'] * 5
    })

# Inisialisasi State untuk Simulasi Real-time
if 'data' not in st.session_state:
    st.session_state.data = generate_worker_data()
if 'alert_triggered' not in st.session_state:
    st.session_state.alert_triggered = False

# --- HEADER ---
st.title("⚡ SentinelPulse")
st.subheader("Regional Workforce Health Early Warning & Dispatch Center")
st.markdown("---")

# --- METRIK UTAMA ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Active Workers Monitored", "4,205", "+12 from last shift")
col2.metric("Ambient WBGT (Camp A)", "32.4 °C", "Extreme Heat", delta_color="inverse")
col3.metric("System Latency", "1.2 ms", "-0.3 ms")
col4.metric("Active Field Alerts", "1" if st.session_state.alert_triggered else "0", 
            color="red" if st.session_state.alert_triggered else "normal")

st.markdown("---")

# --- SIMULASI REAL-TIME & ALERTING ---
st.sidebar.header("🛠️ Simulation Controls")
st.sidebar.markdown("Use this to simulate an incoming anomaly from edge sensors.")

if st.sidebar.button("🚨 Simulate Heat Stress Anomaly (WRK-002)"):
    st.session_state.alert_triggered = True
    
if st.sidebar.button("✅ Resolve Alert"):
    st.session_state.alert_triggered = False
    st.session_state.data = generate_worker_data() # Reset data

# Update data if alert is triggered
if st.session_state.alert_triggered:
    # Injecting critical vitals for WRK-002
    st.session_state.data.loc[1, 'Heart Rate (bpm)'] = np.random.randint(140, 160)
    st.session_state.data.loc[1, 'Skin Temp (°C)'] = np.round(np.random.uniform(38.5, 39.2), 1)
    st.session_state.data.loc[1, 'Status'] = 'CRITICAL'
    
    st.error("⚠️ **URGENT ALERT (Sub-2s SLA):** WRK-002 (Camp A) is showing sustained elevated Heart Rate (>145 bpm) and rising Skin Temp (38.8 °C). Imminent Heat Exhaustion predicted. Dispatching mandatory rest and hydration alert to Field Supervisor...")

# --- GRAFIK & TABEL ---
col_chart, col_table = st.columns([2, 1])

with col_chart:
    st.markdown("#### 📈 Real-Time Vitals Stream (WRK-002)")
    # Bikin data dummy timeseries buat WRK-002
    times = pd.date_range(end=datetime.now(), periods=20, freq='S')
    
    if st.session_state.alert_triggered:
        hr_data = np.concatenate([np.random.randint(80, 100, 15), np.random.randint(140, 160, 5)])
    else:
        hr_data = np.random.randint(80, 100, 20)
        
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=hr_data, mode='lines+markers', name='Heart Rate', line=dict(color='red' if st.session_state.alert_triggered else 'green')))
    fig.update_layout(yaxis_title="BPM", margin=dict(l=0, r=0, t=30, b=0), height=300)
    
    # Red line threshold
    fig.add_hline(y=130, line_dash="dash", line_color="red", annotation_text="Danger Threshold")
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("#### 📋 Live Worker Roster")
    # Tampilkan dataframe dengan styling
    def color_status(val):
        color = 'red' if val == 'CRITICAL' else 'green'
        return f'color: {color}; font-weight: bold'
    
    st.dataframe(st.session_state.data.style.applymap(color_status, subset=['Status']), use_container_width=True, hide_index=True)

# Auto-refresh tipis-tipis buat efek 'live' pas direkam (hilangkan saat recording alert)
if not st.session_state.alert_triggered:
    time.sleep(2)
    st.rerun()
