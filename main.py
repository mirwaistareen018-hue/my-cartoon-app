import streamlit as st
from gtts import gTTS
import os

# Page Config
st.set_page_config(page_title="Long Video Studio PRO", page_icon="🎬", layout="wide")

st.title("Long Video Studio PRO - 5 Min to 1 Hour")
st.write("Original Long Video Maker - No Copyright")

# Sidebar Settings
st.sidebar.header("Settings")
video_length = st.sidebar.select_slider(
    "Select Video Length",
    options=["5 Minutes", "8 Minutes", "15 Minutes", "1 Hour"]
)

scene_count_map = {
    "5 Minutes": 10,
    "8 Minutes": 16,
    "15 Minutes": 30,
    "1 Hour": 100
}
num_scenes = scene_count_map[video_length]
st.sidebar.info(f"Total Scenes: {num_scenes}")

# Main Input
user_idea = st.text_input("Enter Your Story Idea:", "A thirsty crow searching for water")

# Story Logic - English Only
def generate_story(idea, total_scenes):
    story_template = [
        f"The story of {idea} begins, everyone is happy",
        f"Suddenly {idea} faces a big problem",
        f"{idea} goes on a journey to find a solution",
        f"On the way, {idea} meets a new friend",
        f"Both make a clever plan together",
        f"The first attempt fails but they don't give up",
        f"They try again with more effort",
        f"Finally their hard work pays off",
        f"Everyone celebrates and is very happy",
        f"Moral of the story: hard work always wins"
    ]
    
    full_story = []
    for i in range(1, total_scenes + 1):
        line = story_template[(i-1) % len(story_template)]
        full_story.append(f"Scene {i}: {line}.")
    return full_story

# Generate Button
if st.button(f"Generate {video_length} Full Movie", type="primary", use_container_width=True):
    
    if not user_idea:
        st.error("Please enter story idea first!")
    else:
        st.success(f"Generating {video_length} movie with {num_scenes} scenes...")
        
        progress = st.progress(0)
        story_list = generate_story(user_idea, num_scenes)
        
        full_text_for_audio = ""
        container = st.container()
        
        for idx, scene in enumerate(story_list):
            progress.progress((idx + 1) / num_scenes)
            full_text_for_audio += scene + " "
            with container:
                st.write(f"✅ {scene}")

        st.divider()
        st.subheader("Full Script Ready!")
        st.write(full_text_for_audio)

        # Audio Generation
        st.subheader("Generating Audio...")
        try:
            tts = gTTS(text=full_text_for_audio, lang='en', slow=False)
            audio_file = "final_movie_audio.mp3"
            tts.save(audio_file)
            
            st.audio(audio_file)
            
            with open(audio_file, "rb") as f:
                st.download_button(
                    label="Download Final Audio",
                    data=f,
                    file_name=audio_file,
                    mime="audio/mp3",
                    use_container_width=True
                )
            
            st.balloons()
            st.success(f"Done! Your {video_length} movie script and audio is ready!")
            
        except Exception as e:
            st.error(f"Error: {e}")
