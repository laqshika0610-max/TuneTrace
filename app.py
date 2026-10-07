
import streamlit as st
import pandas as pd
import re
from rapidfuzz import fuzz

# Load the song dataset.
songs_df = pd.read_pickle("songs.pkl")

# Clean text for matching.
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# Extract the song title.
def extract_title(filename):
    filename = filename.replace(".txt", "")
    parts = filename.split("#_#")

    if len(parts) >= 2:
        return parts[1].strip()

    return filename.strip()

# Find matching songs.
def find_songs(user_lyric, number_of_results=5):
    clean_user_lyric = clean_text(user_lyric)

    def calculate_score(lyrics):
        words = lyrics.split()
        best_score = 0
        section_length = len(clean_user_lyric.split())

        for i in range(len(words) - section_length + 1):
            section = " ".join(words[i:i + section_length])

            ratio_score = fuzz.ratio(clean_user_lyric, section)
            word_score = fuzz.token_sort_ratio(clean_user_lyric, section)
            partial_score = fuzz.partial_ratio(clean_user_lyric, section)

            score = (
                ratio_score * 0.5 +
                word_score * 0.3 +
                partial_score * 0.2
            )

            if score > best_score:
                best_score = score

        return best_score

    songs_df["match_score"] = songs_df["clean_lyrics"].apply(
        calculate_score
    )

    return songs_df.sort_values(
        by="match_score",
        ascending=False
    ).head(number_of_results)

# Create the app.
st.title("🎵 Hindi Song Finder")

st.write("Enter a lyric and find the song that matches it.")

lyric = st.text_area(
    "Enter a lyric:",
    placeholder="Type a few words from the song..."
)

if st.button("Find Song"):
    if lyric.strip():
        results = find_songs(lyric)

        for _, row in results.iterrows():
            st.subheader(row["title"])
            st.write(f"Year: {row['year']}")
            st.write(f"Match: {row['match_score']:.2f}%")
            st.divider()
    else:
        st.warning("Please enter a lyric first.")
