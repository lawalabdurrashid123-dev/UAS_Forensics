import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="DEMS - Forensic Portal",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Mobile-Friendly Styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #4A90E2;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 0.9rem;
        color: #888888;
        margin-bottom: 20px;
    }
    .stMetric {
        background-color: #1E222A;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #313745;
    }
    </style>
""", unsafe_allow_html=True)

# Database Setup
def init_db():
    conn = sqlite3.connect("dems.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL,
            item_number TEXT NOT NULL,
            investigator TEXT NOT NULL,
            description TEXT,
            file_name TEXT,
            file_hash TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Helper function to compute SHA-256 hash
def get_file_hash(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()

# Fetch DB Stats
def get_stats():
    conn = sqlite3.connect("dems.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(DISTINCT case_id), COUNT(id) FROM evidence")
    cases, items = c.fetchone()
    conn.close()
    return cases, items

# Header Section
st.markdown('<div class="main-header">⚖️ Forensics DEMS</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Digital Evidence Management & Chain of Custody</div>', unsafe_allow_html=True)

# Top Metrics Row
total_cases, total_items = get_stats()
m1, m2, m3 = st.columns(3)
m1.metric("📁 Active Cases", total_cases)
m2.metric("🔍 Logged Items", total_items)
m3.metric("🛡️ Hash Standard", "SHA-256")

st.markdown("---")

# Sidebar Navigation
st.sidebar.title("📌 Menu")
page = st.sidebar.radio("Navigate", ["📥 Ingest Evidence", "🔎 View & Verify Evidence"])

if page == "📥 Ingest Evidence":
    st.subheader("📥 Ingest New Evidence")
    
    with st.container():
        col1, col2 = st.columns([1, 1])
        with col1:
            case_id = st.text_input("Case ID", placeholder="e.g., CASE-2026-004")
            item_number = st.text_input("Item Number / ID", placeholder="e.g., ITEM-01")
            investigator = st.text_input("Investigator / Badge #", placeholder="e.g., Det. Lawal #402")
        
        with col2:
            description = st.text_area("Evidence Description", placeholder="Describe artifact context...")
            uploaded_file = st.file_uploader("Upload Digital Artifact", type=None)

        st.write("")
        if st.button("🔒 Log Evidence & Generate Hash", type="primary", use_container_width=True):
            if case_id and item_number and investigator and uploaded_file:
                file_bytes = uploaded_file.read()
                file_hash = get_file_hash(file_bytes)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                conn = sqlite3.connect("dems.db")
                c = conn.cursor()
                c.execute('''
                    INSERT INTO evidence (case_id, item_number, investigator, description, file_name, file_hash, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (case_id, item_number, investigator, description, uploaded_file.name, file_hash, timestamp))
                conn.commit()
                conn.close()

                st.success(f"✅ Evidence **{item_number}** registered under **{case_id}**!")
                st.code(f"SHA-256: {file_hash}", language="text")
                st.rerun()
            else:
                st.error("⚠️ Please fill in all required fields and attach a file.")

elif page == "🔎 View & Verify Evidence":
    st.subheader("🔎 Chain of Custody & Verification")

    conn = sqlite3.connect("dems.db")
    df = pd.read_sql_query("SELECT case_id, item_number, investigator, file_name, file_hash, timestamp FROM evidence ORDER BY id DESC", conn)
    conn.close()

    if not df.empty:
        st.write("### 📋 Evidence Logs")
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        st.write("### 🛡️ Verify Artifact Integrity")
        
        verify_file = st.file_uploader("Upload File to Audit Hash Match", key="verify")
        if verify_file:
            verify_bytes = verify_file.read()
            computed_hash = get_file_hash(verify_bytes)
            
            st.info(f"**Computed Hash:** `{computed_hash}`")
            
            if computed_hash in df['file_hash'].values:
                matched = df[df['file_hash'] == computed_hash].iloc[0]
                st.success(f"✔️ **INTEGRITY VERIFIED!** Matches Case `{matched['case_id']}`, Item `{matched['item_number']}`.")
            else:
                st.error("🚨 **HASH MISMATCH!** File has been altered or is not logged in the system.")
    else:
        st.info("No evidence items currently logged in the database.")
