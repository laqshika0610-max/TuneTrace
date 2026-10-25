
import streamlit as st
import pandas as pd
import re
from rapidfuzz import fuzz
from urllib.parse import quote_plus

# Set up the app.
st.set_page_config(
    page_title="TuneTrace",
    page_icon="🎵",
    layout="centered"
)

# Load the song dataset.
songs_df = pd.read_pickle("songs.pkl")


# Clean text for matching.
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# Find matching songs.
def find_songs(user_lyric, number_of_results=3):
    clean_user_lyric = clean_text(user_lyric)

    if not clean_user_lyric:
        return songs_df.head(0)

    def calculate_score(lyrics):
        lyrics = str(lyrics)
        words = lyrics.split()
        section_length = len(clean_user_lyric.split())
        best_score = 0

        if not words:
            return 0

        if len(words) < section_length:
            return fuzz.ratio(clean_user_lyric, " ".join(words))

        for i in range(len(words) - section_length + 1):
            section = " ".join(
                words[i:i + section_length]
            )

            ratio_score = fuzz.ratio(
                clean_user_lyric, section
            )
            word_score = fuzz.token_sort_ratio(
                clean_user_lyric, section
            )
            partial_score = fuzz.partial_ratio(
                clean_user_lyric, section
            )

            score = (
                ratio_score * 0.5
                + word_score * 0.3
                + partial_score * 0.2
            )

            best_score = max(best_score, score)

        return best_score

    results = songs_df.copy()

    results["match_score"] = results["clean_lyrics"].apply(
        calculate_score
    )

    return results.sort_values(
        by="match_score",
        ascending=False
    ).head(number_of_results)


# Create the app interface.
st.title("🎵 TuneTrace")
st.subheader("Find any Hindi song from its lyrics")

st.write(
    "Remember a few lines but not the song's name? "
    "Enter the lyrics below to discover your closest matches."
)

lyric = st.text_area(
    "Enter song lyrics",
    placeholder="Type a few words from the song...",
    height=120
)

if st.button("🔍 Find My Song", type="primary"):
    if lyric.strip():
        with st.spinner("Searching the song database..."):
            results = find_songs(lyric, number_of_results=3)

        if results.empty:
            st.warning("No matching songs were found.")
        else:
            st.success("Here are your top 3 matches!")

            for rank, (_, row) in enumerate(
                results.iterrows(), start=1
            ):
                title = str(row["title"])
                year = row["year"]
                score = row["match_score"]

                st.divider()
                st.markdown(f"### {rank}. 🎵 {title}")
                st.write(f"**Year:** {year}")
                st.progress(
                    max(0.0, min(float(score) / 100, 1.0))
                )
                st.write(f"**Match: {score:.2f}%**")

                search_query = quote_plus(
                    f"{title} {year} Hindi Bollywood song"
                )
                youtube_url = (
                    "https://www.youtube.com/results?search_query="
                    + search_query
                )

                st.link_button(
                    "▶️ Search on YouTube",
                    youtube_url
                )
    else:
        st.warning("Please enter some lyrics first.")

st.caption(
    "TuneTrace uses text matching to suggest songs. "
    "Please check the results to confirm the correct song."
)

