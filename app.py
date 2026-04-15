import streamlit as st
import google.generativeai as genai
import easyocr
import numpy as np
from PIL import Image
import pandas as pd
import json
import os
from dotenv import load_dotenv

# --- 1. SETUP GEMINI (SECURE) ---
os.environ["GOOGLE_API_USE_MTLS_ENDPOINT"] = "never" 
load_dotenv() 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    st.error("⚠️ API Key missing! Check Streamlit Secrets.")

model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. CLEANING LOGIC (KEEPING YOUR ORIGINAL LOGIC) ---
def clean_val(val):
    if not val or str(val).lower() in ["none", "n/a", "null", "[]"]:
        return "-"
    if isinstance(val, list):
        val = ", ".join([str(i) for i in val])
    if isinstance(val, dict):
        val = ", ".join([f"{k}: {v}" for k, v in val.items()])
    clean = str(val).replace("*", "").replace("[", "").replace("]", "").replace("'", "").replace('"', "")
    return clean.strip()

# --- 3. UI SETUP ---
st.set_page_config(page_title="CS&GT Automation", layout="wide", page_icon="📊")

# Custom CSS for a Professional Look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover { background-color: #0056b3; color: white; }
    .status-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR (Clean UI movement) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1486/1486433.png", width=80) # Generic Data Icon
    st.title("Control Panel")
    st.info("Upload the poster and any extra text to generate the Excel row.")
    
    uploaded_file = st.file_uploader("Upload Poster (JPG/PNG)", type=["jpg", "png", "jpeg"])
    # CHANGED: Optional Text Input
    extra_text = st.text_area("Paste Extra Text (Optional)", placeholder="Paste caption or links here...")
    
    process_btn = st.button("🚀 RUN EXTRACTION")
    st.divider()
    st.caption("CS&GT Event Automation v2.0")

# --- MAIN CONTENT AREA ---
st.title("📊 CS&GT Event Data Extractor")
st.write("Transform event posters into structured department data instantly.")

if not uploaded_file:
    st.warning("Please upload a poster in the sidebar to begin.")
    # Show a placeholder image or instruction
    st.image("https://fyi.org.nz/assets/placeholder-666327e0544520786967733230c144e311f974eb178652427a1c3df42ca488a0.png", width=300)

if process_btn and uploaded_file:
    col1, col2 = st.columns([1.2, 0.8])
    
    with col1:
        with st.spinner("🧠 AI is analyzing patterns..."):
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
            - Instagram_Link: Extract the URL only.

            Context: {ocr_result} {extra_text}
            
            JSON Keys: Date, Venue, Time, Event_Type, Topic, Convenor, Co_Convenor, Event_Coordinators, Student_Coordinators, Chief_Guest, Designation_Details, Instagram_Link.
            """
            
            try:
                response = model.generate_content(prompt)
                data = json.loads(response.text[response.text.find('{'):response.text.rfind('}')+1])
                
                headers = [
                    "S.No", "Department", "Date of the Event", "Venue", "Timing of the Event", 
                    "Name of the Event", "Topic of the Event", 
                    "Convenor", "Co-convenor", "Event Coordinator's", 
                    "Student Coordinators", "Name of the Chief Guest", 
                    "Designation & Company details", "Instagram Link"
                ]
                
                # Handling the link logic (keeping your logic)
                raw_link = data.get("Instagram_Link", extra_text)
                clean_link = raw_link.split(" ")[0] if raw_link else "-"
                
                row_data = [
                    "1", "CS&GT", 
                    clean_val(data.get("Date")), clean_val(data.get("Venue")),
                    clean_val(data.get("Time")), clean_val(data.get("Event_Type")),
                    clean_val(data.get("Topic")), clean_val(data.get("Convenor")),
                    clean_val(data.get("Co_Convenor")), clean_val(data.get("Event_Coordinators")),
                    clean_val(data.get("Student_Coordinators")), clean_val(data.get("Chief_Guest")),
                    clean_val(data.get("Designation_Details")),
                    clean_val(clean_link if "http" in clean_link.lower() or "instagr" in clean_link.lower() else "-")
                ]
                
                st.success("✅ Extraction Complete!")

                # --- THE GRID (YOUR ORIGINAL HTML) ---
                safe_row_data = [str(val).replace("&", "&amp;") for val in row_data]
                html_grid = f"""
                <div style="width: 100%; border: 1px solid #444; overflow-x: auto; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                    <table style="width: 100%; border-collapse: collapse; font-family: 'Segoe UI', Arial; font-size: 13px; min-width: 1200px;">
                        <tr style="background-color: #2c3e50; color: white; font-weight: bold;">
                            {" ".join([f'<th style="border: 1px solid #444; padding: 12px; text-align: center;">{h}</th>' for h in headers])}
                        </tr>
                        <tr style="background-color: white; color: black;">
                            {" ".join([f'<td style="border: 1px solid #ddd; padding: 12px; text-align: left; vertical-align: top;">{val}</td>' for val in safe_row_data])}
                        </tr>
                    </table>
                </div>
                """
                st.markdown(html_grid, unsafe_allow_html=True)
                st.info("💡 **Tip:** Highlight the row above with your mouse, Copy (Ctrl+C), and Paste directly into Excel.")

                st.divider()
                with st.expander("🔍 Debug Raw Extracted Data"):
                    st.json(data)
            
            except Exception as e:
                st.error(f"AI Parsing Error: {e}")

    with col2:
        st.subheader("🖼️ Processed Poster")
        st.image(uploaded_file, use_container_width=True)
