# ⚡ SentinelPulse: Real-Time Workforce Health Early Warning System

> Submission for the **Future Health Digital Innovation Challenge**  
> **Track:** Population and Workforce Health Early Warning  

SentinelPulse is an event-driven telemetry and syndromic anomaly detection platform designed to protect industrial workers in extreme climates from acute heat strain, physical collapse, and communicable outbreak clusters.

---

## 🏛️ System Architecture

![SentinelPulse Architecture](assets/architecture.png)

The platform employs a **5-Tier Enterprise Cloud Architecture**:
1. **Edge & Telemetry Ingestion Layer:** Aggregates streams from COTS smartbands (PPG heart rate, thermistors, accelerometer), microclimate WBGT nodes, and on-site clinic records.
2. **Secure Cloud Gateway:** Azure Event Hubs with TLS 1.3 transport, partitioned message broker, and dead-letter queues (DLQ).
3. **Analytics & Governance Engine:** Salted cryptographic tokenization for PII stripping (UAE PDPL/DoH compliant) + deterministic multi-factor physiological hysteresis engine.
4. **Persistence & Lake Tier:** Azure Notification Hubs (emergency dispatch), TimescaleDB/Azure Cosmos DB (hot vitals), and cold aggregated health lakehouse.
5. **Action & Response Tier:** Sub-2s push alert notifications to field supervisors and regional syndromic command center for ADPHC.

---

## 🚀 Quickstart (Local Deployment)

```bash
# Clone the repository
git clone [https://github.com/](https://github.com/)<your-username>/sentinelpulse.git
cd sentinelpulse

# Install dependencies
pip install -r requirements.txt

# Run the command center dashboard
streamlit run app.py

🛡️ Privacy & Compliance
Zero PII Leakage: Worker civil identifiers are decoupled at Tier 3 ingestion.

Explainable Triage: Pure deterministic clinical logic based on OSHA/NIOSH threshold standards to eliminate false alarms and avoid automated AI hallucinations.