
import streamlit as st
import pandas as pd
import re
from rapidfuzz import fuzz
from urllib.parse import quote_plus
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="TuneTrace",
    page_icon="🎵",
    layout="centered"
)

# Load the song database.
songs_df = pd.read_pickle("songs.pkl")

# Clean text before matching.
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# Find the closest matching songs.
def find_songs(user_lyric, number_of_results=3):
    query = clean_text(user_lyric)

    if not query:
        return pd.DataFrame()

    query_words = query.split()
    section_length = len(query_words)
    results = songs_df.copy()

    def calculate_score(lyrics):
        words = clean_text(lyrics).split()

        if not words:
            return 0.0

        if len(words) < section_length:
            return fuzz.ratio(query, " ".join(words))

        best_score = 0.0

        for i in range(len(words) - section_length + 1):
            section = " ".join(
                words[i:i + section_length]
            )

            score = (
                fuzz.ratio(query, section) * 0.5
                + fuzz.token_sort_ratio(query, section) * 0.3
                + fuzz.partial_ratio(query, section) * 0.2
            )

            best_score = max(best_score, score)

        return best_score

    results["match_score"] = results["clean_lyrics"].apply(
        calculate_score
    )

    return results.sort_values(
        "match_score", ascending=False
    ).head(number_of_results)


# Save user corrections for later review.
def save_feedback(song_title, artist, lyrics, comments):
    file_path = Path("feedback.csv")

    feedback = pd.DataFrame([{
        "date": datetime.now().isoformat(timespec="seconds"),
        "suggested_song": song_title,
        "artist": artist,
        "lyrics_searched": lyrics,
        "comments": comments
    }])

    feedback.to_csv(
        file_path,
        mode="a",
        header=not file_path.exists(),
        index=False,
        encoding="utf-8"
    )


# App interface.
st.title("🎵 TuneTrace")
st.subheader("Find Hindi songs using their lyrics")

st.write(
    "Remember a few lines but not the song's name? "
    "Enter them below to find your closest matches."
)

lyric = st.text_area(
    "Enter song lyrics",
    placeholder="Type a few words from the song...",
    height=120,
    key="lyrics_input"
)

if st.button("🔍 Find My Song", type="primary"):
    if lyric.strip():
        with st.spinner("Searching the song database..."):
            results = find_songs(lyric, 3)

        st.session_state["results"] = results
        st.session_state["searched_lyrics"] = lyric.strip()
    else:
        st.warning("Please enter some lyrics first.")

# Display the top three results.
if "results" in st.session_state:
    results = st.session_state["results"]
    searched_lyrics = st.session_state.get(
        "searched_lyrics", ""
    )

    if results.empty:
        st.warning("No matching songs were found.")
    else:
        st.success("Your top 3 song matches")

        for rank, (_, row) in enumerate(
            results.iterrows(), start=1
        ):
            title = str(row["title"])
            year = row["year"]
            score = float(row["match_score"])

            st.divider()
            st.subheader(f"{rank}. 🎵 {title}")
            st.write(f"**Year:** {year}")
            st.progress(max(0.0, min(score / 100, 1.0)))
            st.write(f"**Match score:** {score:.2f}%")

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

    # Let users report missing or incorrect matches.
    st.divider()
    st.subheader("🤔 Couldn't find your song?")
    st.write(
        "Tell us which song you were looking for. "
        "Your suggestion can help us improve TuneTrace."
    )

    with st.form("correction_form"):
        suggested_song = st.text_input(
            "Correct song title (if known)"
        )

        artist = st.text_input(
            "Artist or singer (optional)"
        )

        correction_lyrics = st.text_area(
            "Lyrics you searched",
            value=searched_lyrics
        )

        comments = st.text_area(
            "What went wrong? (optional)",
            placeholder="For example, the correct song was not listed."
        )

        submitted = st.form_submit_button(
            "Submit Correction"
        )

        if submitted:
            if not suggested_song.strip() and not comments.strip():
                st.warning(
                    "Please enter a song title or describe the issue."
                )
            else:
                try:
                    save_feedback(
                        suggested_song.strip(),
                        artist.strip(),
                        correction_lyrics.strip(),
                        comments.strip()
                    )
                    st.success(
                        "Thank you! Your feedback has been recorded."
                    )
                except Exception:
                    st.error(
                        "Feedback could not be saved. "
                        "Please try again later."
                    )

st.caption(
    "Match scores indicate text similarity, not guaranteed accuracy. "
    "Please check the results before choosing a song."
)

