import pickle
import os
from pathlib import Path

import requests
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
POSTER_PLACEHOLDER = 'https://via.placeholder.com/500x750?text=No+Poster'


st.set_page_config(
    page_title='Movie Recommender System',
    layout='wide',
    initial_sidebar_state='collapsed',
)


def get_tmdb_api_key():
    api_key = os.getenv('TMDB_API_KEY')

    if api_key:
        return api_key

    try:
        return st.secrets.get('TMDB_API_KEY')
    except (FileNotFoundError, KeyError):
        return None


def load_pickle_file(path):
    first_bytes = path.read_bytes()[:64]

    if first_bytes.startswith(b'version https://git-lfs.github.com/spec'):
        raise RuntimeError(
            f'{path.name} is a Git LFS pointer file, not the real model file. '
            'Run git lfs pull before building or starting the app.'
        )

    with open(path, 'rb') as pickle_file:
        return pickle.load(pickle_file)


@st.cache_resource
def load_data():
    return (
        load_pickle_file(BASE_DIR / 'movies.pkl'),
        load_pickle_file(BASE_DIR / 'similrity.pkl'),
    )


@st.cache_data(show_spinner=False)
def fetch_poster(movie_id, api_key):
    if not api_key:
        return POSTER_PLACEHOLDER

    url = f'https://api.themoviedb.org/3/movie/{movie_id}'
    params = {
        'api_key': api_key,
        'language': 'en-US',
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return POSTER_PLACEHOLDER

    poster_path = data.get('poster_path')

    if not poster_path:
        return POSTER_PLACEHOLDER

    return f'https://image.tmdb.org/t/p/w500{poster_path}'


def recommend(movie_title, movies, similarity, api_key, total_recommendations=5):
    movie_matches = movies[movies['title'] == movie_title]

    if movie_matches.empty:
        return []

    movie_index = movie_matches.index[0]
    distances = similarity[movie_index]
    recommended_indexes = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda item: item[1],
    )[1:total_recommendations + 1]

    recommendations = []

    for index, _score in recommended_indexes:
        movie = movies.iloc[index]
        recommendations.append({
            'title': movie['title'],
            'poster': fetch_poster(movie['movie_id'], api_key),
        })

    return recommendations


try:
    movies, similarity = load_data()
except RuntimeError as error:
    st.error(str(error))
    st.stop()

movie_titles = movies['title'].values
tmdb_api_key = get_tmdb_api_key()

st.markdown(
    """
    <style>
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title('Movie Recommender System')

selected_movie = st.selectbox(
    'Select your movie',
    movie_titles,
)

if st.button('Recommend'):
    recommended_movies = recommend(selected_movie, movies, similarity, tmdb_api_key)

    if recommended_movies:
        if not tmdb_api_key:
            st.info('TMDB_API_KEY is not set on this server. Posters will load after the Docker container is started with that environment variable.')

        st.subheader('Recommended movies')
        columns = st.columns(len(recommended_movies))

        for column, movie in zip(columns, recommended_movies):
            with column:
                st.image(movie['poster'])
                st.write(movie['title'])
    else:
        st.warning('No recommendations found for this movie.')
