import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import os

# --- DATABASE SETUP ---
DB_FILE = "dems_database.db"
STORAGE_DIR = "evidence_vault"

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL,
            item_number TEXT NOT NULL,
            description TEXT,
            filename TEXT,
            file_hash TEXT,
            uploaded_by TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- HELPER FUNCTIONS ---
def calculate_hash(file_bytes):
    """Generates a SHA-256 hash for data integrity."""
    return hashlib.sha256(file_bytes).hexdigest()

def save_evidence(case_id, item_number, description, filename, file_bytes, uploaded_by):
    """Saves file to disk and logs metadata to SQLite."""
    # 1. Calculate Hash
    file_hash = calculate_hash(file_bytes)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 2. Save File safely
    safe_filename = f"{case_id}_{item_number}_{filename}"
    file_path = os.path.join(STORAGE_DIR, safe_filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)
        
    # 3. Log to DB
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO evidence (case_id, item_number, description, filename, file_hash, uploaded_by, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (case_id, item_number, description, safe_filename, file_hash, uploaded_by, timestamp))
    conn.commit()
    conn.close()
    return file_hash

def get_all_evidence():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM evidence ORDER BY id DESC", conn)
    conn.close()
    return df

# --- STREAMLIT UI ---
st.set_page_config(page_title="Digital Evidence Management System", page_icon="⚖️", layout="wide")

st.title("⚖️ Digital Evidence Management System (DEMS)")
st.caption("Secure Ingestion, Chain of Custody Tracking, and Integrity Verification")
st.markdown("---")

# Sidebar Navigation
menu = ["📥 Ingest Evidence", "🔍 View Chain of Custody", "🛡️ Verify Evidence Integrity"]
choice = st.sidebar.selectbox("Navigation Menu", menu)

# --- MODULE 1: INGEST EVIDENCE ---
if choice == "📥 Ingest Evidence":
    st.header("Log New Evidence Item")
    
    col1, col2 = st.columns(2)
    with col1:
        case_id = st.text_input("Case ID (e.g., CASE-2026-004)")
        item_number = st.text_input("Item Number / ID (e.g., ITEM-01)")
        uploaded_by = st.text_input("Investigator Name / Badge #")
        
    with col2:
        description = st.text_area("Evidence Description")
        uploaded_file = st.file_uploader("Upload Digital Evidence (Image, Video, Doc, etc.)")

    if st.button("Securely Log Evidence", type="primary"):
        if case_id and item_number and uploaded_by and uploaded_file:
            file_bytes = uploaded_file.read()
            
            # Process and save
            with st.spinner("Calculating cryptographic hash and securing file..."):
                generated_hash = save_evidence(
                    case_id, item_number, description, uploaded_file.name, file_bytes, uploaded_by
                )
                
            st.success("🎉 Evidence successfully logged and secured!")
            st.info(f"**Generated SHA-256 Hash:** `{generated_hash}`")
            st.warning("⚠️ Any alteration to this file will completely change this cryptographic hash.")
        else:
            st.error("Please fill out all fields and upload a file.")

# --- MODULE 2: VIEW CHAIN OF CUSTODY ---
elif choice == "🔍 View Chain of Custody":
    st.header("Audit Log & Chain of Custody")
    
    df = get_all_evidence()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        # Download log feature
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Audit Log to CSV", data=csv, file_name="chain_of_custody_log.csv", mime="text/csv")
    else:
        st.info("No evidence has been logged in the system yet.")

# --- MODULE 3: VERIFY INTEGRITY ---
elif choice == "🛡️ Verify Evidence Integrity":
    st.header("Verify File Integrity")
    st.write("Upload a file to check if it matches an existing item in the database. If even a single pixel or character has changed, the verification will fail.")
    
    verify_file = st.file_uploader("Upload file to verify")
    
    if verify_file:
        test_bytes = verify_file.read()
        calculated_hash = calculate_hash(test_bytes)
        
        st.write(f"**Calculated Hash:** `{calculated_hash}`")
        
        # Check against DB
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM evidence WHERE file_hash = ?", (calculated_hash,))
        result = c.fetchone()
        conn.close()
        
        if result:
            st.success("✅ **MATCH FOUND! Integrity Verified.**")
            st.balloons()
            
            # Display matching details
            st.markdown(f"""
            - **Case ID:** {result[1]}
            - **Item ID:** {result[2]}
            - **Original Investigator:** {result[6]}
            - **Timestamp logged:** {result[7]}
            """)
        else:
            st.error("❌ **NO MATCH FOUND. This file has either been modified or was never logged in this system.**")