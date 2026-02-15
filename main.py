import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

# --- 1. CONFIGURATION & FILE SETUP ---
UPLOAD_DIR = "resumes"
DATABASE_NAME = "job_tracker.db"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    # Table includes company, position, status, date added, and the resume file path
    c.execute('''CREATE TABLE IF NOT EXISTS jobs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  company TEXT, 
                  position TEXT, 
                  status TEXT, 
                  date_added TEXT, 
                  resume_path TEXT)''')
    conn.commit()
    return conn

# --- 2. DATABASE ACTIONS ---
def add_job_to_db(company, position, status, date, resume_path):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO jobs (company, position, status, date_added, resume_path) VALUES (?, ?, ?, ?, ?)",
               (company, position, status, str(date), resume_path))
    conn.commit()
    conn.close()

def update_job_status(job_id, current_status):
    flow = ["To Apply", "Applied", "Interviewing", "Offer"]
    try:
        current_index = flow.index(current_status)
        if current_index < len(flow) - 1:
            new_status = flow[current_index + 1]
            conn = sqlite3.connect(DATABASE_NAME)
            c = conn.cursor()
            c.execute("UPDATE jobs SET status = ? WHERE id = ?", (new_status, job_id))
            conn.commit()
            conn.close()
            st.rerun()
    except ValueError:
        pass

def delete_job(job_id):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    st.rerun()

# --- 3. UI LAYOUT ---
st.set_page_config(page_title="Career Organizer", layout="wide", page_icon="😉")
st.title("JOB TRACKER")
st.markdown("---")

# Sidebar: Form to add new jobs
with st.sidebar:
    st.header("👌 Add New Job")
    with st.form("job_form", clear_on_submit=True):
        company = st.text_input("Company Name", placeholder="e.g. Google")
        position = st.text_input("Job Title", placeholder="e.g. Python Developer")
        status = st.selectbox("Current Stage", ["To Apply", "Applied", "Interviewing", "Offer"])
        uploaded_file = st.file_uploader("Upload Tailored Resume", type=['pdf', 'docx'])
        date = st.date_input("Date Discovered", value=datetime.now())
        
        submit = st.form_submit_button("Save to Pipeline")
        
        if submit:
            if company and position:
                resume_name = None
                if uploaded_file:
                    # Clean filename and save to /resumes folder
                    resume_name = f"{company}_{position}_{uploaded_file.name}".replace(" ", "_")
                    with open(os.path.join(UPLOAD_DIR, resume_name), "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                add_job_to_db(company, position, status, date, resume_name)
                st.success(f"Added {position} at {company}!")
                st.rerun()
            else:
                st.error("Please provide both Company and Position.")

# --- 4. THE KANBAN BOARD ---
conn = init_db()
df = pd.read_sql_query("SELECT * FROM jobs", conn)
conn.close()

# Define the columns for the funnel
statuses = ["To Apply", "Applied", "Interviewing", "Offer"]
cols = st.columns(len(statuses))

for i, status_type in enumerate(statuses):
    with cols[i]:
        st.subheader(f"📍 {status_type}")
        
        # --- NEW LOGIC STARTS HERE ---
        # 1. Filter the dataframe for jobs matching THIS column's status
        current_jobs = df[df['status'] == status_type]
        
        # 2. Loop through those specific jobs and draw a card for each
        for _, row in current_jobs.iterrows():
            with st.container(border=True):
                st.markdown(f"### {row['company']}")
                st.write(f"**Role:** {row['position']}")
                st.caption(f"📅 {row['date_added']}")
                
                # Action Buttons
                btn_col1, btn_col2 = st.columns(2)
                
                # Move to next stage
                if status_type != "Offer":
                    if btn_col1.button("➡️ Next", key=f"next_{row['id']}"):
                        update_job_status(row['id'], row['status'])
                
                # Delete entry
                if btn_col2.button("🗑️", key=f"del_{row['id']}"):
                    delete_job(row['id'])
                
                # Resume Button
                if row['resume_path']:
                    file_path = os.path.join(UPLOAD_DIR, row['resume_path'])
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label="📄 Resume",
                                data=f,
                                file_name=row['resume_path'],
                                key=f"dl_{row['id']}",
                                use_container_width=True
                            )


