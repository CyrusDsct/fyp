#demo
import streamlit as st
import requests

# Page configuration
st.set_page_config(page_title="Map Audit System", layout="wide")
st.title("Map Analysis Dashboard")

# --- API Configuration ---
API_BASE_URL = "http://127.0.0.1:5000"

# --- Sidebar: Separate Upload Section ---
st.sidebar.header("Upload Center")

# MAP SECTION
st.sidebar.subheader("🗺️ Upload Map")
map_file = st.sidebar.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'], key="map_uploader")
if st.sidebar.button("Save Map to DB"):
    if map_file:
        with st.spinner('Uploading Map...'):
            files = {"file": (map_file.name, map_file.getvalue(), map_file.type)}
            response = requests.post(f"{API_BASE_URL}/uploadImage", files=files)
            if response.status_code == 200:
                st.sidebar.success("✅ Map Uploaded!")
                st.rerun()

st.sidebar.divider()

# CSV SECTION
st.sidebar.subheader("📊 Upload Data")
csv_file = st.sidebar.file_uploader("Choose a CSV", type=['csv'], key="csv_uploader")
if st.sidebar.button("Save CSV to DB"):
    if csv_file:
        with st.spinner('Uploading CSV...'):
            files = {"file": (csv_file.name, csv_file.getvalue(), csv_file.type)}
            response = requests.post(f"{API_BASE_URL}/uploadImage", files=files)
            if response.status_code == 200:
                st.sidebar.success("✅ CSV Uploaded!")
                st.rerun()

# --- Main Screen---
st.header("Database Gallery")

# Fetching data
try:
    response = requests.get(f"{API_BASE_URL}/readImage")
    if response.status_code == 200:
        data = response.json().get("data", [])
        
        if not data:
            st.info("No files found in MongoDB.")
        else:
            cols = st.columns(3)
            for idx, img in enumerate(data):
                with cols[idx % 3]:
                    # Check if it's a CSV or Image
                    if img['original_name'].lower().endswith('.csv'):
                        st.info(f"📄 **CSV Data File**\n\n{img['original_name']}")
                    else:
                        full_url = f"{API_BASE_URL}{img['url']}"
                        st.image(full_url, caption=img['original_name'], use_container_width=True)
                        
                        # --- Analyze button ---
                        if st.button(f"🔍 Analyze Map", key=f"analyze_{img['_id']}"):
                            with st.spinner('AI analyzing map...'):
                                ana_res = requests.post(f"{API_BASE_URL}/analyzeMap/{img['_id']}")
                                if ana_res.status_code == 200:
                                    # Store results to show on screen
                                    st.session_state['analysis_result'] = ana_res.json().get("analysis")
                                    st.session_state['analysis_target'] = img['original_name']
                                else:
                                    st.error("Analysis failed. Please check backend.")
                    
                    # --- DELETE SECTION ---
                    # using the image_id
                    if st.button(f"🗑️ Delete Image", key=f"del_{img['_id']}"):
                        with st.spinner('Deleting...'):
                            del_res = requests.delete(f"{API_BASE_URL}/deleteImage/{img['_id']}")
                            if del_res.status_code == 200:
                                st.success("Deleted!")
                                st.rerun() 
                            else:
                                st.error("Failed to delete")
                    
                    st.caption(f"ID: {img['_id']}")
except Exception as e:
    st.error(f"Connection Error: {e}")

# --- Analysis Section ---
st.divider()
st.subheader("Statistical Analysis")

# Outputs the results directly to our screen
if 'analysis_result' in st.session_state:
    st.success(f"Analysis complete for: {st.session_state['analysis_target']}")
    # Displaying in markdown
    st.markdown("### AI Report")
    st.text_area("JSON Output", st.session_state['analysis_result'], height=400)
    
    if st.button("Clear Results"):
        del st.session_state['analysis_result']
        st.rerun()
else:
    st.info("Click 'Analyze Map' on any image above to see the results here.")