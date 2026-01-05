import streamlit as st
import requests

# Page configuration
st.set_page_config(page_title="Map Audit System", layout="wide")
st.title("Map Analysis Dashboard")

# --- API Configuration ---
# Keeping the local address for development
API_BASE_URL = "http://127.0.0.1:5000"

# --- Sidebar: Upload Function ---
st.sidebar.header("Upload New Map")
uploaded_file = st.sidebar.file_uploader("Choose an image file", type=['png', 'jpg', 'jpeg'])

if st.sidebar.button("Upload to MongoDB"):
    if uploaded_file is not None:
        with st.spinner('Uploading...'):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                response = requests.post(f"{API_BASE_URL}/uploadImage", files=files)
                if response.status_code == 200:
                    st.sidebar.success("✅ Upload Successful!")
                    st.rerun() 
                else:
                    st.sidebar.error(f"❌ Upload Failed: {response.text}")
            except Exception as e:
                st.sidebar.error(f"Connection Error: {e}")

# --- Main Screen---
st.header("Database Image Gallery")

# Fetching data from your GET API
try:
    response = requests.get(f"{API_BASE_URL}/readImage")
    if response.status_code == 200:
        data = response.json().get("data", [])
        
        if not data:
            st.info("No images found in MongoDB.")
        else:
            # Displaying images in a grid layout
            cols = st.columns(3)
            for idx, img in enumerate(data):
                with cols[idx % 3]:
                    # Full image URL
                    full_url = f"{API_BASE_URL}{img['url']}"
                    st.image(full_url, caption=img['original_name'], use_container_width=True)
                    
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
    else:
        st.error("Failed to fetch data from MongoDB")
except Exception as e:
    st.error(f"Could not connect to Flask: {e}")

# --- Analysis Section ---
st.divider()
st.subheader("Statistical Analysis")
st.info("Will connect to LLM API soon.")