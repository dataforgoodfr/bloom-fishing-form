import streamlit as st
import pandas as pd
import itertools
import numpy as np
import os
from PIL import Image
from supabase import create_client, Client
import uuid

from dotenv import load_dotenv
load_dotenv()

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------

st.set_page_config(page_title="Fishing Classification", page_icon="🎣", layout="centered", initial_sidebar_state="collapsed", menu_items=None)

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("styles.css")

# SIDEBAR

# st.sidebar.image("https://upload.wikimedia.org/wikipedia/fr/e/e8/Logo_BLOOM.jpg",use_column_width=True)

image_folder_path = "assets/images"


# ----------------------------------------------------------------------
# RESSOURCES
# ----------------------------------------------------------------------


@st.cache_resource
def get_client_supabase():
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    client: Client = create_client(url, key)
    return client

def log_result(client,language,first_name,last_name,email,option_left,option_right,n_trials,result,source = ""):

    # Generate result uuid
    # result_uuid = str(uuid.uuid4())

    record = {
        "language":language,
        "first_name":first_name,
        "last_name":last_name,
        "email":email,
        "option_left":option_left,
        "option_right":option_right,
        "n_trials":n_trials,
        "result":result,
        "source":source,
    }

    print("Logging record:",record)
    data, count = client.table('records').insert(record).execute()
    return data,count

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
        "content":"Pour chaque couple d'engins de pêche, cliquez sur celui que vous percevez comme ayant le plus d'impact négatif sur l'environnement.\n\nIl faut approximativement 30-40 minutes pour compléter le questionnaire, mais à tout moment, vous pouvez le quitter. Vos réponses seront sauvegardées.",
    },
    "EN":{
        "title":"What is your perception of the impact of different fishing gears on marine ecosystems?",
        "content":"For each pair of fishing gears, click on the one you perceive as having the most negative impact on the environment.\n\nIt takes approximately 30-40 minutes to complete the questionnaire, but at any time, you can leave it. Your answers will be saved.",
    },
}


@st.cache_data
def load_data(lang):
    data = pd.read_excel("assets/descriptions_engins.xlsx").head(27)
    mapping = data[["name","path_image"]].set_index("name")["path_image"].to_dict()
    mapping_images = {k:load_image(v) for k,v in mapping.items()}
    mapping_data = data.set_index("name").T.to_dict()
    return mapping_images,mapping_data

def log_user(language,first_name,last_name,email):

    if all([language, first_name, last_name, email]):

        print(language,first_name,last_name,email)
        st.session_state.language = language
        st.session_state.first_name = first_name
        st.session_state.last_name = last_name
        st.session_state.email = email
        st.session_state.started = True
        st.session_state.date = pd.Timestamp.now()
    
    else:
        if language == "English":
            st.error("Please fill in all the fields.")
        else:
            st.error("Veuillez remplir tous les champs.")


def get_existing_combinations(email):

    # Assuming 'supabase' is your Supabase client
    data, count = client.table('records').select('*').eq('email', email).execute()
    data = pd.DataFrame(data[1])

    # Get the combinations
    existing_combinations = {frozenset([row['winner'], row['loser']]) for _, row in data.iterrows()}

    return existing_combinations
    

# ----------------------------------------------------------------------
# LOGIN
# ----------------------------------------------------------------------



if "started" not in st.session_state:

    _,col_image,_ = st.columns([1,2,1])
    col_image.image("assets/images/1-CHALUT BENTHIQUE A PANNEAUX-transparent.png")
    title = st.container()

    language = st.selectbox("Language", ["English", "Français"])
    lang = "EN" if language == "English" else "FR"
    with title:
        st.write(f"### {content[lang]['title']}")

    first_name = st.text_input("First name" if lang == "EN" else "Prénom")
    last_name = st.text_input("Last name" if lang == "EN" else "Nom")
    email = st.text_input("Email" if lang == "EN" else "Email")
    start = st.button("Start" if lang == "EN" else "Commencer",on_click=log_user,args=(language,first_name,last_name,email))


# ----------------------------------------------------------------------
# EXPERIMENT
# ----------------------------------------------------------------------


else:
    # Display user information in the sidebar if they've started
    user = {
        "language":st.session_state.language,
        "first_name":st.session_state.first_name,
        "last_name":st.session_state.last_name,
        "email":st.session_state.email,
        "date":st.session_state.date,
    }

    language = st.session_state.language
    lang = "EN" if language == "English" else "FR"

    st.sidebar.write("### Logged in as:" if lang == "EN" else "### Connecté en tant que:")
    st.sidebar.write(user["first_name"])
    st.sidebar.write(user["last_name"])
    st.sidebar.write(user["email"])


    # Load the data and the client for the database using cached resources
    client = get_client_supabase()
    mapping_images,mapping_data = load_data(lang)
    values = list(mapping_data.keys())

    # Generate all the combinations of the data
    if "combinations" not in st.session_state:
        combinations = list(itertools.combinations(values,2))
        np.random.shuffle(combinations)
    else:
        combinations = st.session_state.combinations

    # Get the index of the current question
    if "index" not in st.session_state:
        st.session_state["index"] = 0
    index = st.session_state["index"]

    if index == 0:

        existing_combinations = get_existing_combinations(user["email"])

        if len(existing_combinations) > 0:

            # Filter out combinations from the list if they are in the set of existing combinations
            new_combinations = [combo for combo in combinations if frozenset(combo) not in existing_combinations]
            new_index = len(combinations) - len(new_combinations)
            combinations = new_combinations
            st.session_state["combinations"] = combinations


    # Display the title and the content
    st.write(f"### {content[lang]['title']}")
    st.info(content[lang]["content"])

    # Get the two options
    combination = list(combinations[index])
    np.random.shuffle(combination)
    id1,id2 = combination
    option1 = mapping_data[id1][lang]
    option2 = mapping_data[id2][lang]

    # Get the title and the description of the options
    # Parse the string to get the title and the description
    title1,desc1 = option1.split(":",1)
    title2,desc2 = option2.split(":",1)
    title1 = title1.strip()
    title2 = title2.strip()
    desc1 = desc1.strip().capitalize()
    desc2 = desc2.strip().capitalize()

    # Get the images
    image1 = mapping_images[id1]
    image2 = mapping_images[id2]


    def validate_option(record):

        query_params = st.experimental_get_query_params()
        if "utm_source" in query_params:
            source = query_params["utm_source"][0]
        else:
            source = ""

        # Get the result and find the technique id
        option_left = record["option_left"]
        option_right = record["option_right"]
        result = record["result"]
        n_trials = record["n_trials"]
        print(record)

        # Get the user information
        language = st.session_state.language
        first_name = st.session_state.first_name
        last_name = st.session_state.last_name
        email = st.session_state.email

        # Log the result in the database
        log_result(client,language,first_name,last_name,email,option_left,option_right,n_trials,result,source)

        # Update the session state
        st.session_state["last_result"] = record
        st.session_state["index"] += 1


    # Get the button message depending on the language
    message_button = "Has the most impact" if lang == "EN" else "A le plus d'impact" 

    # Display the two options and the images
    col1,col0,col2 = st.columns([2,1,2])

    with col1:
        st.image(image1,use_column_width=True)
    with col0:
        pass
    with col2:
        st.image(image2,use_column_width=True)

    col1,col0,col2 = st.columns(3)

    with col1:
        submitted1 = st.button(f"{message_button}",on_click=validate_option, args=({"option_left":id1,"option_right":id2,"n_trials":index,"result":"left"},),key = "button1",use_container_width = True)
        st.markdown(f"#### {title1}\n{desc1}")
    with col0:
        st.button("Same impact" if lang == "EN" else "Même impact",on_click=validate_option, args=({"option_left":id1,"option_right":id2,"n_trials":index,"result":"same"},),key = "button0",use_container_width = True)
    with col2:
        submitted2 = st.button(f"{message_button}",on_click=validate_option, args=({"option_left":id1,"option_right":id2,"n_trials":index,"result":"right"},),key = "button2",use_container_width = True)
        st.markdown(f"#### {title2}\n{desc2}")


    st.progress(index/len(combinations),text=f"{'Progress' if lang == 'EN' else 'Avancement'}: {index}/{len(combinations)}")
    # st.write(f"{'Progress' if lang == 'EN' else 'Avancement'}: {index}/{len(combinations)}")

