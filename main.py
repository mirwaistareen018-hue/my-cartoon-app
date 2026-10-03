import streamlit as st
from gtts import gTTS
import io

st.set_page_config(page_title="Cocomelon PRO English", page_icon="🌈", layout="centered")

st.markdown("""
<style>
.stage {background: linear-gradient(to bottom, #87CEEB, #FFF9C4); padding:30px; border-radius:30px; border:5px solid #FF4081; text-align:center;}
.lyrics {background:white; padding:20px; border-radius:15px; font-size:20px; font-weight:bold; color:#333; white-space:pre-line; line-height:1.6;}
.char-big {font-size:90px;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#FF0000;'>🌈 Cocomelon PRO MAX - 100% ENGLISH 🌈</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Viral Videos for Kids & Family - USA Audience</p>", unsafe_allow_html=True)

st.subheader("Step 1: Choose Cartoon")
col1, col2 = st.columns(2)
with col1:
    main_char = st.selectbox("Main Hero", ["Cat", "Dog", "Bunny", "Lion", "Elephant", "Monkey", "Baby Shark", "Bird"])
with col2:
    friends = st.multiselect("Friends", ["Cat", "Dog", "Bunny", "Lion", "Elephant", "Monkey"], default=["Dog"])

char_name = st.text_input("Hero Name", "Mimi")

st.subheader("Step 2: Choose Viral Topic")
rhyme_style = st.selectbox("Trending Topic 2026", [
    "Johnny Johnny Yes Papa",
    "Twinkle Twinkle Little Star",
    "Wheels on the Bus",
    "Baby Shark Dance",
    "Moral Story - Honest Woodcutter",
    "Funny Ghost Story",
    "ABC Phonics Song"
])

music_style = st.selectbox("Music Style", ["Happy Piano - Cocomelon", "Fun Guitar", "Soft Lullaby", "Dance Beat"])
speed = st.select_slider("Voice Speed", options=["Slow", "Normal", "Fast"], value="Normal")

if st.button("🚀 CREATE VIRAL VIDEO", use_container_width=True, type="primary"):
    
    all_friends = ", ".join(friends) if friends else "friends"
    main_emoji = "🐱" 

    if "Johnny" in rhyme_style:
        rhyme_text = f"Johnny Johnny Yes Papa?\nEating sugar? No Papa!\nTelling lies? No Papa!\nOpen your mouth Ha Ha Ha!\n\n{char_name} {char_name} Yes Papa?\nDancing now? Yes Papa!\nHaving fun? Yes Papa!\nWe love you Ha Ha Ha!\n\nDance dance dance with {all_friends}!"
    
    elif "Twinkle" in rhyme_style:
        rhyme_text = f"Twinkle Twinkle Little Star,\nHow I wonder what you are!\nUp above the world so high,\n{char_name} the {main_char} is in the sky!\n\nTwinkle Twinkle {char_name} Star,\nYou are my Super Star!\nShine with {all_friends}!"
    
    elif "Wheels" in rhyme_style:
        rhyme_text = f"The wheels on the bus go round and round,\nRound and round, round and round!\n{char_name} on the bus goes jump jump jump!\n\nThe horn on the bus goes beep beep beep!\n{all_friends} goes clap clap clap!\nLets go to the zoo!"
    
    elif "Shark" in rhyme_style:
        rhyme_text = f"Baby Shark doo doo doo doo doo doo,\nBaby Shark doo doo doo doo doo doo!\n{char_name} Shark doo doo doo doo doo doo!\nLets dance doo doo doo!\n\nMama Shark doo doo doo,\nPapa Shark doo doo doo,\n{all_friends} doo doo doo!\nRun away doo doo doo!"
    
    elif "Moral" in rhyme_style:
        rhyme_text = f"Once upon a time, {char_name} the {main_char} was very honest.\n{char_name} found a golden axe in the jungle.\nBut {char_name} said, No, this is not mine.\nThe angel was happy and gave {char_name} a magic gift!\nMoral: Honesty is the best policy!\n{all_friends} lived happily!"
    
    elif "Ghost" in rhyme_style:
        rhyme_text = f"One funny night, {char_name} met a friendly little ghost!\nBoo said the ghost, but {char_name} laughed Ha Ha Ha!\nThe ghost was not scary, he wanted to dance!\nSo {char_name} and {all_friends} danced together!\nFunny funny night, everyone became friends!"
    
    else:
        rhyme_text = f"{char_name} loves to learn ABC,\nA B C D dance with me!\nOne two three, count with {all_friends},\nYes yes yes we love to learn!\nWash wash wash your hands,\nBrush brush brush your teeth!\nHooray! We had fun today!"

    st.markdown(f"<div class='stage'><div class='char-big'>🌟</div><h2>{char_name} & {all_friends}</h2><div class='lyrics'>{rhyme_text}</div><p>Music: {music_style} | Speed: {speed}</p></div>", unsafe_allow_html=True)

    try:
        is_slow = True if speed == "Slow" else False
        tts = gTTS(text=rhyme_text, lang='en', slow=is_slow)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        st.audio(fp, format="audio/mp3")
        st.download_button("📥 DOWNLOAD MP3 FOR YOUTUBE", fp, file_name=f"{char_name}_Viral.mp3", mime="audio/mp3", use_container_width=True)
        st.balloons()
        st.success("Done! Ready for YouTube!")
    except Exception as e:
        st.error(f"Audio Error: {e}")

st.info("TIP: This is Fixed Final Version - No Error - 100% English for USA audience.")
