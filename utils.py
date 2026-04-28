import streamlit as st
import base64

def set_background(image_path: str, opacity: float = 0.3):
    with open(image_path, "rb") as f:
        img_data = f.read()

    b64 = base64.b64encode(img_data).decode()
    ext = image_path.split(".")[-1]

    css = f"""
    <style>
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: url("data:image/{ext};base64,{b64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        opacity: {opacity};
        z-index: 0;
        pointer-events: none;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
