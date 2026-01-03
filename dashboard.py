import streamlit as st
import requests
import pandas as pd

# Page configuration
st.set_page_config(page_title="Map Audit System", layout="wide")
st.title("Map Audit - Python Dashboard")

# --- Sidebar: Upload Function ---
st.sidebar.header("Upload New Map")
uploaded_file = st.sidebar.file_uploader("Choose an image file", type=['png', 'jpg', 'jpeg'])

if st.sidebar.button("Upload to MongoDB"):
    if uploaded_file is not None:
        with st.spinner('Uploading...'):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                response = requests.post("http://127.0.0.1:5000/uploadImage", files=files)
                if response.status_code == 200:
                    st.sidebar.success("✅ Upload Successful!")
                    st.rerun() # Refresh to show the new image
                else:
                    st.sidebar.error(f"❌ Upload Failed: {response.text}")
            except Exception as e:
                st.sidebar.error(f"Connection Error: {e}")

# --- Main Screen ---
st.header("Database Image Gallery")
if st.button("🔄 Refresh Gallery"):
    # Fetching data from your GET API
    try:
        response = requests.get("http://127.0.0.1:5000/readImage")
        if response.status_code == 200:
            data = response.json().get("data", [])
            
            if not data:
                st.info("No images found in MongoDB.")
            else:
                # Displaying images in a grid layout
                cols = st.columns(3)
                for idx, img in enumerate(data):
                    with cols[idx % 3]:
                        # Ensure the URL points to local Flask server
                        full_url = f"http://127.0.0.1:5000{img['url']}"
                        st.image(full_url, caption=img['original_name'], use_container_width=True)
                        st.caption(f"Database ID: {img['_id']}")
        else:
            st.error("Failed to fetch data from MongoDB")
    except Exception as e:
        st.error(f"Could not connect to Flask: {e}")

# --- Analysis Section  ---
st.divider()
st.subheader("Statistical Analysis")

