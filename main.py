import streamlit as st
from gtts import gTTS
import re, random

st.set_page_config(page_title="Auto Cartoon Singer", page_icon="??")
st.markdown("<h1 style='text-align:center; color:#FF1493;'>?? Auto Cartoon Singing App ??</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Type story -> Auto Song -> Characters Dance & Sing</p>", unsafe_allow_html=True)

prompt = st.text_input("? Type your story / names (e.g. cat and rat):", "cat and rat")

def get_chars(p):
    found = re.findall(r'\b(cat|rat|dog|rabbit|lion|bear|duck|bird|monkey)\b', p.lower())
    if not found:
        found = [w for w in p.split() if len(w)>2][:2]
        if not found: found = ["cat","rat"]
    return [c.title() for c in found]

if prompt:
    chars = get_chars(prompt)
    st.success(f"?? Auto Detected: {' & '.join(chars)} - Names changed!")
    
    n1, n2 = (chars + ["Friend"])[:2]
    lyrics = f"""{n1} and {n2} dancing in the sun,
Singing la la, having so much fun!
Jump and hop, one two three,
{n1} loves {n2}, you and me!"""

    col1, col2 = st.columns([2,1])
    with col1:
        st.subheader("?? Auto Generated Song")
        st.markdown(f"<div style='background:white; padding:20px; border-radius:15px; font-size:18px; white-space:pre-line; border-left:5px solid #FF1493;'>{lyrics}</div>", unsafe_allow_html=True)
        
        # Auto voice
        try:
            tts = gTTS(text=lyrics, lang='en', slow=False)
            tts.save("song.mp3")
            st.audio("song.mp3", autoplay=True)
            st.balloons()
        except Exception as e:
            st.warning(f"Voice will work after internet ok: {e}")

    with col2:
        st.subheader("?? Stage")
        emojis = {"Cat":"??","Rat":"??","Dog":"??","Rabbit":"??","Lion":"??","Bear":"??","Duck":"??"}
        for c in chars:
            st.markdown(f"<div style='background:white; border-radius:20px; padding:15px; text-align:center; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'><div style='font-size:60px;'>{emojis.get(c,'?')}</div><h3>{c}</h3><p>?? Dancing & ?? Singing</p></div><br>", unsafe_allow_html=True)

st.caption("Everything automatic: Type -> Song -> Voice -> Dance | Like YouTube Nursery Rhymes")