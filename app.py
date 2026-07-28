import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Digital Evidence Management System (DEMS)",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Desktop & Mobile
st.markdown("""
    <style>
    h1 {
        font-size: clamp(1.6rem, 4vw, 2.5rem) !important;
        font-weight: 700 !important;
    }
    div.stButton > button[kind="primary"] {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
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

# SHA-256 Calculation
def get_file_hash(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()

# Navigation Menu (Split into 3 distinct items)
st.sidebar.markdown("### Navigation Menu")
page = st.sidebar.selectbox(
    "",
    ["Ingest Evidence", "View Chain of Custody", "Verify Integrity"],
    label_visibility="collapsed"
)

# Title & Subtitle
st.title("⚖️ Digital Evidence Management System (DEMS)")
st.caption("Secure Ingestion, Chain of Custody Tracking, and Integrity Verification")
st.markdown("---")

# Page 1: Ingest Evidence
if page == "Ingest Evidence":
    st.header("Log New Evidence Item")
    
    col1, col2 = st.columns(2)
    
    with col1:
        case_id = st.text_input("Case ID (e.g., CASE-2026-004)")
        item_number = st.text_input("Item Number / ID (e.g., ITEM-01)")
        investigator = st.text_input("Investigator Name / Badge #")
        
    with col2:
        description = st.text_area("Evidence Description", height=130)
        uploaded_file = st.file_uploader("Upload Digital Evidence (Image, Video, Doc, etc.)", type=None)

    st.write("")
    if st.button("Securely Log Evidence", type="primary"):
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

            st.success(f"✅ Evidence **{item_number}** successfully logged under **{case_id}**!")
            st.code(f"SHA-256 Hash: {file_hash}", language="text")
        else:
            st.error("⚠️ Please fill in all fields and attach an evidence file.")

# Page 2: View Chain of Custody
elif page == "View Chain of Custody":
    st.header("Chain of Custody Directory")

    conn = sqlite3.connect("dems.db")
    df = pd.read_sql_query("SELECT case_id, item_number, investigator, description, file_name, file_hash, timestamp FROM evidence ORDER BY id DESC", conn)
    conn.close()

    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No evidence records found in the database.")

# Page 3: Verify Integrity
elif page == "Verify Integrity":
    st.header("Verify File Integrity")
    st.write("Upload a digital file to verify its SHA-256 hash against the database ledger.")

    conn = sqlite3.connect("dems.db")
    df = pd.read_sql_query("SELECT case_id, item_number, file_hash FROM evidence", conn)
    conn.close()

    verify_file = st.file_uploader("Upload File to Verify SHA-256 Hash", key="audit")
    
    if verify_file:
        verify_bytes = verify_file.read()
        computed_hash = get_file_hash(verify_bytes)
        
        st.info(f"Calculated SHA-256 Hash: `{computed_hash}`")
        
        if not df.empty and computed_hash in df['file_hash'].values:
            match = df[df['file_hash'] == computed_hash].iloc[0]
            st.success(f"✔️ **INTEGRITY VERIFIED!** Matches Case `{match['case_id']}`, Item `{match['item_number']}`.")
        else:
            st.error("🚨 **INTEGRITY WARNING!** Hash mismatch or unrecorded file.")
