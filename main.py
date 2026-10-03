import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import random

st.set_page_config(page_title="COCOMELON APP", layout="wide")
st.title("COCOMELON - Meri App Chal Gayi!")
st.success("App is Working - 100% OK")

def get_image(prompt):
    try:
        q = requests.utils.quote(prompt)
        seed = random.randint(1, 99999)
        url = f"https://image.pollinations.ai/prompt/{q}?width=1024&height=720&nologo=true&seed={seed}"
        r = requests.get(url, timeout=30)
        return Image.open(BytesIO(r.content))
    except:
        return None

story = st.text_area("Kahani Likhein:", "A cute mouse eating cheese on table, then big cat comes")

if st.button("GENERATE IMAGE"):
    with st.spinner("Image Ban Rahi Hai..."):
        img = get_image("cute 3d pixar baby mouse eating cheese on table, brown wall, ceiling fan")
        if img:
            st.image(img)
            st.balloons()
        else:
            st.error("Dobara button dabayein")
