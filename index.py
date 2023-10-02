import streamlit as st
import pandas as pd
import itertools
import numpy as np
import fnmatch
import os
from PIL import Image


st.set_page_config(page_title="Bloom", page_icon="🎣", layout="centered", initial_sidebar_state="expanded", menu_items=None)

# SIDEBAR

st.sidebar.image("https://upload.wikimedia.org/wikipedia/fr/e/e8/Logo_BLOOM.jpg",use_column_width=True)
st.sidebar.title("Bloom")

language = st.sidebar.selectbox("Language",["English", "Français"])

name = st.sidebar.text_input("Name")
surname = st.sidebar.text_input("Surname")
email = st.sidebar.text_input("Email")

image_folder_path = "assets/images"

def load_image(path):

    th = 0.3

    # Open the original image
    original_image = Image.open(os.path.join(image_folder_path,path))

    # Get the original size of the image
    original_size = original_image.size

    # Calculate the new size of the image
    new_size = (int(original_size[0] * th), int(original_size[1] * th))

    # Resize the image to the new size
    resized_image = original_image.resize(new_size)
    return np.array(resized_image)


@st.cache_data
def load_data(language):
    data = pd.read_excel("assets/descriptions_engins.xlsx").head(27)
    lang = "FR" if language == "Français" else "EN"
    mapping = data[[lang,"path_image"]].set_index(lang)["path_image"].to_dict()
    mapping = {k:load_image(v) for k,v in mapping.items()}
    return mapping,data


mapping,data = load_data(language)
values = list(mapping.keys())

combinations = list(itertools.combinations(values,2))
np.random.shuffle(combinations)

if "index" not in st.session_state:
    st.session_state["index"] = 0
    index = 0
else:
    index = st.session_state["index"]

with st.form(key = "my_form"):

    option1,option2 = combinations[index]

    title1,desc1 = option1.split(":",1)
    title2,desc2 = option2.split(":",1)
    title1 = title1.strip()
    title2 = title2.strip()
    desc1 = desc1.strip().capitalize()
    desc2 = desc2.strip().capitalize()

    image1 = mapping[option1]
    image2 = mapping[option2]

    # image1 = os.path.join(image_folder_path,mapping[option1])
    # image2 = os.path.join(image_folder_path,mapping[option2])
    # assert os.path.exists(image1), f"Image {image1} does not exist"


    col1,col2 = st.columns(2)

    with col1:
        st.image(image1,use_column_width=True)
        st.markdown(f"#### {title1}\n{desc1}")
    with col2:
        st.image(image2,use_column_width=True)
        st.markdown(f"#### {title2}\n{desc2}")

    col3,col4 = st.columns(2)
    
    with col3:
        submitted = st.form_submit_button("Option 1")
        if submitted:
            st.session_state["index"] += 1
            index += 1

    with col4:
        submitted = st.form_submit_button("Option 2")
        if submitted:
            st.session_state["index"] += 1
            index += 1



    st.write(f"Progress: {index}/{len(combinations)}")





