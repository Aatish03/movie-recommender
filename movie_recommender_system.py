import streamlit as st
import pickle
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

url_new = 'https://github.com/username/repository/releases/download/tag/similarity.pkl'
download_path = 'path/to/save/similarity.pkl'

response = requests.get(url_new)
with open(download_path, 'wb') as f:
    f.write(response.content)


def fetch_poster(movie_id, retries=3, backoff_factor=0.3):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}?language=en-US&api_key=eec5e61786f3230bfbdc78f343f532d5'

    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    try:
        response = session.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if 'poster_path' in data:
            return "https://image.tmdb.org/t/p/w300/" + data['poster_path']
        else:
            st.error(f"Poster path not found for movie ID: {movie_id}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from TMDB API: {e}")
        return None

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movies_posters = []

    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        poster = fetch_poster(movie_id)
        if poster:
            recommended_movies_posters.append(poster)
        else:
            recommended_movies_posters.append("https://via.placeholder.com/300")
    return recommended_movies, recommended_movies_posters

# Load the data
movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Streamlit app
st.title('Movie Recommender System')

selected_movie_name = st.selectbox(
    'Enter Movie Name',
    movies['title'].values)

if st.button('Recommend'):
    names, posters = recommend(selected_movie_name)

    # Create columns to display movies in rows of 3
    for i in range(0, len(names), 3):
        cols = st.columns(3)
        for col, name, poster in zip(cols, names[i:i+3], posters[i:i+3]):
            with col:
                st.markdown(
                    f"""
                    <div style='text-align: center; font-size: 16px; font-weight: bold; max-height: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;' title='{name}'>
                        {name}
                    </div>
                    """, 
                    unsafe_allow_html=True)
                st.image(poster, use_column_width=True)
                st.write("---")
