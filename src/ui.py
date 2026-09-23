
import base64
import streamlit as st

def background_local(imagem):
    with open(imagem, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(
        f"""<style>
        .stApp {{
            background-image: url(data:image/png;base64,{encoded});
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* Borda do file uploader */
        [data-testid="stFileUploaderDropzone"] {{
            border: 2px solid #79911D !important;
            border-radius: 8px;
        }}

        /* Borda dos checkboxes */
       div.stCheckbox span[data-baseweb="checkbox"] > div {{
        border: 2px solid #79911D !important;
        }}

        /* Borda do botão de download */
        [data-testid="stBaseButton-secondary"] {{
            border: 2px solid #79911D !important;
            border-radius: 6px;
        }}
        </style>""",
        unsafe_allow_html=True
    )

def formatar_dif(valor):
    if valor > 0:
        return "background-color: lightgreen"
    elif valor < 0:
        return "background-color: lightcoral"
    return ""
   
   
   
def adicionar_logo_header(caminho):
    with open(caminho, "rb") as arquivo:
        logo = base64.b64encode(arquivo.read()).decode()

    st.markdown(
        f"""
        <style>
            [data-testid="stHeader"] {{
                background-image: url("data:image/png;base64,{logo}");
                background-repeat: no-repeat;
                background-position: center center;
                background-size: 200px auto;
            }}
        </style>
        """,
        unsafe_allow_html=True
    )