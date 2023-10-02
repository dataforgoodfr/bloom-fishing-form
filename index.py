import streamlit as st
import pandas as pd
import itertools
import numpy as np
import os
from PIL import Image


st.set_page_config(page_title="Bloom", page_icon="🎣", layout="centered", initial_sidebar_state="collapsed", menu_items=None)

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("styles.css")

# SIDEBAR

# st.sidebar.image("https://upload.wikimedia.org/wikipedia/fr/e/e8/Logo_BLOOM.jpg",use_column_width=True)

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


content = {
    "FR":{
        "title":"Quelle est votre perception de l'impact des différents engins de pêche sur les écosystèmes marins ?",
        "content":"Pour chaque couple d'engins de pêche, cliquez sur celui que vous percevez comme ayant le plus d'impact négatif sur l'environnement.\n\nIl faut approximativement 20-25 minutes pour compléter le questionnaire, mais à tout moment, vous pouvez le quitter et y revenir plus tard. Vos réponses seront sauvegardées.",
    },
    "EN":{
        "title":"What is your perception of the impact of different fishing gears on marine ecosystems?",
        "content":"For each pair of fishing gears, click on the one you perceive as having the most negative impact on the environment.\n\nIt takes approximately 20-25 minutes to complete the questionnaire, but at any time, you can leave it and come back later. Your answers will be saved.",
    },
}



@st.cache_data
def load_data(lang):
    data = pd.read_excel("assets/descriptions_engins.xlsx").head(27)
    mapping = data[[lang,"path_image"]].set_index(lang)["path_image"].to_dict()
    mapping = {k:load_image(v) for k,v in mapping.items()}
    return mapping,data

def log_user(language,name,surname,email):

    if all([language, name, surname, email]):

        print(language,name,surname,email)
        st.session_state.language = language
        st.session_state.name = name
        st.session_state.surname = surname
        st.session_state.email = email
        st.session_state.started = True
        st.session_state.date = pd.Timestamp.now()
    
    else:
        if language == "English":
            st.error("Please fill in all the fields.")
        else:
            st.error("Veuillez remplir tous les champs.")

if "started" not in st.session_state:
    title = st.container()
    language = st.selectbox("Language", ["English", "Français"])
    lang = "EN" if language == "English" else "FR"
    with title:
        st.write(f"### {content[lang]['title']}")

    name = st.text_input("First name / Prénom")
    surname = st.text_input("Last name / Nom")
    email = st.text_input("Email")
    start = st.button("Start",on_click=log_user,args=(language,name,surname,email))
else:
    # Display user information in the sidebar if they've started

    user = {
        "language":st.session_state.language,
        "name":st.session_state.name,
        "surname":st.session_state.surname,
        "email":st.session_state.email,
        "date":st.session_state.date,
    }

    st.sidebar.write(user["name"])
    st.sidebar.write(user["surname"])
    language = st.session_state.language
    lang = "EN" if language == "English" else "FR"

    mapping,data = load_data(lang)
    values = list(mapping.keys())

    combinations = list(itertools.combinations(values,2))
    np.random.shuffle(combinations)


    if "index" not in st.session_state:
        st.session_state["index"] = 0
    index = st.session_state["index"]

    st.write(f"### {content[lang]['title']}")
    st.info(content[lang]["content"])

    # if "last_result" in st.session_state:
    #     st.write(st.session_state['last_result'])


    combination = list(combinations[index])
    np.random.shuffle(combination)
    option1,option2 = combination

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


    def validate_option(result):
        print(result)
        st.session_state["last_result"] = result
        st.session_state["index"] += 1


    message_button = "Is more damaging" if lang == "EN" else "Est plus destructeur" 

    col1,col2 = st.columns(2)

    with col1:
        st.image(image1,use_column_width=True)
        submitted1 = st.button(f"{message_button}",on_click=validate_option, args=({"winner":option1,"loser":option2,"n_trials":index},),key = "button1")
        st.markdown(f"#### {title1}\n{desc1}")
    with col2:
        st.image(image2,use_column_width=True)
        submitted2 = st.button(f"{message_button}",on_click=validate_option, args=({"winner":option2,"loser":option1,"n_trials":index},),key = "button2")
        st.markdown(f"#### {title2}\n{desc2}")


    st.write(f"Progress: {index}/{len(combinations)}")

