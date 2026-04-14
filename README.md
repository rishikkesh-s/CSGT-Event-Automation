# CSGT-Event-Automation

**AI-Powered Poster Extraction & Data Management System**

CSGT Event Automation is a specialized tool built to streamline the process of capturing event details from promotional posters. By combining Computer Vision (OCR) and Generative AI, it transforms messy image data into structured, Excel-ready formats in seconds.

## Live Link
https://cs-gt-event-automation.streamlit.app/

---

## Key Features
* **Vision-to-Text:** Uses **EasyOCR** to accurately detect and extract text strings from uploaded posters/images.
* **Intelligent Parsing:** Powered by **Gemini 2.5 Flash** to analyze raw text and categorize it into 14 specific data columns.
* **Optimized for Excel:** Features a custom "Data Grid" interface designed for seamless copy-pasting into Department Master Sheets.
* **Zero Manual Entry:** Eliminates the need for administrative staff to manually type details from images, reducing human error.

## The Tech Stack
* **Frontend/Hosting:** Streamlit (Cloud Deployment)
* **Artificial Intelligence:** Google Gemini 2.5 Flash API
* **Optical Character Recognition:** EasyOCR (Python-based)
* **Data Handling:** Pandas & NumPy

## Project Structure
* `app.py` - The core application engine and Streamlit UI.
* `requirements.txt` - Configuration for the Python environment.
* `.gitignore` - Security protocols to protect private API keys.

---

## 🔧 How to Run Locally
1. Clone the repository:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/CSGT-event-automation.git](https://github.com/YOUR_USERNAME/CSGT-event-automation.git)
