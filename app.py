import streamlit as st
import google.generativeai as genai
import easyocr
import numpy as np
from PIL import Image
import pandas as pd
import json
import os
from dotenv import load_dotenv  # Add this to handle the hidden key

# --- 1. SETUP GEMINI (SECURE) ---
# Forced environment fix to stop the 404 Beta error
os.environ["GOOGLE_API_USE_MTLS_ENDPOINT"] = "never" 

load_dotenv()  # This pulls the key from your secret .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    st.error("⚠️ API Key missing! Make sure it is in your .env file or Streamlit Secrets.")

# Stable 2.0 version
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. CLEANING LOGIC ---
def clean_val(val):
    """Squashes lists/dicts into text and removes bolding."""
    if not val or str(val).lower() in ["none", "n/a", "null", "[]"]:
        return "-"
    
    # If AI returns a list or dict, turn it into a string
    if isinstance(val, list):
        val = ", ".join([str(i) for i in val])
    if isinstance(val, dict):
        val = ", ".join([f"{k}: {v}" for k, v in val.items()])
        
    # Remove bold stars and brackets
    clean = str(val).replace("*", "").replace("[", "").replace("]", "").replace("'", "").replace('"', "")
    return clean.strip()

# --- 3. UI SETUP ---
st.set_page_config(page_title="Dept Event Extractor", layout="wide")
st.title("📋 CS&GT Event Data Extractor")
st.write("Upload a poster and get a clean Excel row instantly.")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Upload Poster (JPG/PNG)", type=["jpg", "png", "jpeg"])
    # CHANGE 1: Renamed from Social Media Link to Paste Raw Text
    raw_text_input = st.text_area("Paste Raw Text (Optional)", placeholder="Paste caption or extra details here...")
    process_btn = st.button("🚀 Extract Row")


# --- 4. PROCESSING ---
if process_btn and uploaded_file:
    with st.spinner("🧠 AI is analyzing the poster..."):
        img = Image.open(uploaded_file)
        reader = easyocr.Reader(['en'])
        ocr_result = " ".join(reader.readtext(np.array(img), detail=0))
        
        prompt = f"""
        Extract details from this text into a SINGLE-LEVEL JSON object.
        Rules:
        - Date: DD.MM.YYYY.
        - Staff (Convenor/Co_Convenor/Coordinators): MUST include names AND titles (e.g., 'Dr. Name, AP/CS&GT').
        - Chief_Guest: Name ONLY.
        - Designation_Details: ONLY the Chief Guest's company/role.
        - Instagram_Link: Extract the Instagram/Social Media URL only. DO NOT include meeting links.

        Context: {ocr_result} {raw_text_input}
        
        JSON Keys: Date, Venue, Time, Event_Type, Topic, Convenor, Co_Convenor, Event_Coordinators, Student_Coordinators, Chief_Guest, Designation_Details, Instagram_Link.
        """
        
        try:
            response = model.generate_content(prompt)
            data = json.loads(response.text[response.text.find('{'):response.text.rfind('}')+1])
            
            headers = [
                "S.No", "Department", "Date of the Event", "Venue", "Timing of the Event", 
                "Name of the Event (Webinar/Guest Lecture/Seminar/Workshop)", "Topic of the Event", 
                "Convenor", "Co-convenor", "Event Coordinator's", 
                "Student Coordinators (IF ANY)", "Name of the Chief Guest", 
                "Designation & Company details", "Instagram Link"
            ]
            
            # CHANGE 2: Logic to ensure ONLY Instagram/Social links are accepted, filtering out Meet/Zoom
            raw_link = data.get("Instagram_Link", "")
            if any(x in raw_link.lower() for x in ["instagram.com", "facebook.com", "linkedin.com", "t.me"]):
                clean_link = raw_link.split(" ")[0]
            else:
                clean_link = "-"
            
            # --- THE FIX: Using 'CS&GT' safely for HTML ---
            row_data = [
                "1", 
                "CS&GT", 
                clean_val(data.get("Date")),
                clean_val(data.get("Venue")),
                clean_val(data.get("Time")),
                clean_val(data.get("Event_Type")),
                clean_val(data.get("Topic")),
                clean_val(data.get("Convenor")),
                clean_val(data.get("Co_Convenor")),
                clean_val(data.get("Event_Coordinators")),
                clean_val(data.get("Student_Coordinators")),
                clean_val(data.get("Chief_Guest")),
                clean_val(data.get("Designation_Details")),
                clean_val(clean_link)
            ]
            
            st.success("✅ Fixed! All 14 boxes are separated.")

            # --- THE GRID (Ensuring & doesn't break the boxes) ---
            safe_row_data = [str(val).replace("&", "&amp;") for val in row_data]

            html_grid = f"""
            <div style="width: 100%; border: 1px solid #444; overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-family: 'Segoe UI', Arial; font-size: 13px; table-layout: fixed;">
                    <tr style="background-color: #DDEBF7; color: black; font-weight: bold;">
                        {" ".join([f'<th style="border: 1px solid #999; padding: 10px; text-align: center; word-wrap: break-word;">{h}</th>' for h in headers])}
                    </tr>
                    <tr style="background-color: white; color: black;">
                        {" ".join([f'<td style="border: 1px solid #999; padding: 10px; text-align: left; vertical-align: top; word-wrap: break-word;">{val}</td>' for val in safe_row_data])}
                    </tr>
                </table>
            </div>
            """
            
            st.markdown(html_grid, unsafe_allow_html=True)
            st.caption("Drag mouse across the boxes above and press Ctrl+C.")

            st.divider()

            with st.expander("🔍 View Details as List"):
                for h, v in zip(headers, row_data):
                    st.write(f"**{h}:** {v}")
            
        except Exception as e:
            st.error(f"Error: {e}")

with col2:
    if uploaded_file:
        st.subheader("🖼️ Poster Preview")
        st.image(uploaded_file, use_container_width=True)
