import streamlit as st
from gtts import gTTS
import io
import random

st.set_page_config(page_title="Cocomelon Studio PRO - English", page_icon="🌈", layout="centered")

st.markdown("""
<style>
.stage {background: linear-gradient(to bottom, #87CEEB, #FFF9C4); padding:30px; border-radius:30px; border:5px solid #FF4081; text-align:center;}
.lyrics {background:white; padding:20px; border-radius:15px; font-size:22px; font-weight:bold; color:#333; white-space:pre-line; line-height:1.6;}
.char-big {font-size:90px;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#FF0000;'>🌈 Cocomelon PRO MAX Studio - 100% ENGLISH 🌈</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Create Viral YouTube Videos For Kids & Family - All in English</p>", unsafe_allow_html=True)

# --- 1. CHARACTERS ---
st.subheader("Step 1: Choose Your Cartoon Characters")
col1, col2 = st.columns(2)
with col1:
    main_char = st.selectbox("Main Hero", ["🐱 Cat", "🐶 Dog", "🐰 Bunny", "🦁 Lion", "🐘 Elephant", "🐵 Monkey", "🦈 Baby Shark", "🐦 Bird"])
with col2:
    friends = st.multiselect("Choose Friends", ["🐱 Cat", "🐶 Dog", "🐰 Bunny", "🦁 Lion", "🐘 Elephant", "🐵 Monkey"], default=["🐶 Dog"])

char_name = st.text_input("Enter Hero Name (e.g. Mimi, Bruno)", "Mimi")

# --- 2. VIRAL TOPICS ---
st.subheader("Step 2: Choose Viral Story / Rhyme")
rhyme_style = st.selectbox("Viral Topic - Trending in 2026",
[
"Johnny Johnny Yes Papa - Cocomelon Style",
"Twinkle Twinkle Little Star",
"Wheels on the Bus - With Animals",
"Baby Shark Dance - Viral",
"Bath Song - Wash Your Hands",
"Yes Yes Vegetables Song - Healthy Food",
"Moral Story - Honest Woodcutter with Animals",
"Funny Horror Story - Friendly Ghost & Monkey (For All Ages)",
"ABC Phonics & Numbers Song"
])

music_style = st.selectbox("Music Style", ["Happy Piano - Cocomelon", "Fun Guitar Beat", "Soft Lullaby", "Upbeat Dance"])
speed = st.select_slider("Voice Speed", options=["Slow", "Normal", "Fast"], value="Normal")

# --- 3. GENERATE ---
if st.button("🚀 CREATE VIRAL VIDEO - FINAL", use_container_width=True, type="primary"):

    all_chars_text = char_name + " and " + ", ".join(friends) if friends else char_name
    main_emoji = main_char.split(" ")[0]

    # --- 100% ENGLISH LYRICS ---
    if "Johnny" in rhyme_style:
        rhyme = f"""Johnny Johnny Yes Papa?
Eating sugar? No Papa!
Telling lies? No Papa!
Open your mouth Ha Ha Ha!

{char_name} {char_name} Yes Papa?
Dancing now? Yes Papa!
Having fun? Yes Papa!
We love you Ha Ha Ha!

La la la... Dance dance dance... Clap clap clap...
{all_chars_text} are happy today!
Jump jump and dance!
"""
    elif "Twinkle" in rhyme_style:
        rhyme = f"""Twinkle Twinkle Little Star,
How I wonder what you are!
Up above the world so high,
{main_emoji} {char_name} is in the sky!

Twinkle Twinkle {char_name} Star,
You are my Super Star!
Shine shine shine all night,
{all_chars_text} loves your light!
"""
    elif "Wheels" in rhyme_style:
        rhyme = f"""The wheels on the bus go round and round,
Round and round, round and round!
{char_name} on the bus goes jump jump jump,
Jump jump jump!

The horn on the bus goes beep beep beep,
{all_chars_text} goes clap clap clap!
Let's go to the zoo!
"""
    elif "Shark" in rhyme_style:
        rhyme = f"""Baby Shark doo doo doo doo doo doo,
Baby Shark doo doo doo doo doo doo!
{char_name} Shark doo doo doo doo doo doo,
Let's dance doo doo doo doo doo doo!

Mama Shark doo doo doo...
Papa Shark doo doo doo...
{all_chars_text} doo doo doo!
Run away doo doo doo!
"""
    elif "Moral" in rhyme_style:
        rhyme = f"""Once upon a time, {char_name} the {main_char} was very honest.
{char_name} found a golden axe in the jungle.
But {char_name} said, No, this is not mine.
The angel was happy and gave {char_name} a magic gift!
Moral of the story: Honesty is the best policy!
{all_chars_text} lived happily ever after!
"""
    elif "Horror" in rhyme_style:
        rhyme = f"""One funny night, {char_name} met a friendly little ghost!
Boo! said the ghost, but {char_name} laughed Ha Ha Ha!
The ghost was not scary, he wanted to dance!
So {all_chars_text} and the ghost danced together!
Boo boo boo... La la la... Funny
