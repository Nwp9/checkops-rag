import streamlit as st
import requests

st.title("AI Playground Backend Demo")

st.write("Test des capacités IA (texte et image)")

# Choix du type
input_type = st.selectbox("Type de donnée", ["text", "image"])

# Choix de la tâche
if input_type == "text":
    task = st.selectbox("Tâche", ["summarize", "explain", "classify"])
else:
    task = st.selectbox("Tâche", ["describe", "ocr"])

# Input utilisateur
data = st.text_area("Entrez votre donnée (texte ou URL d'image)")

# Bouton
if st.button("Analyser"):

    payload = {
        "type": input_type,
        "task": task,
        "data": data
    }

    response = requests.post(
        "http://127.0.0.1:8000/analyze",
        json=payload
    )

    if response.status_code == 200:
        result = response.json()

        st.subheader("Résultat")

        if "output" in result:
            st.write(result["output"])

        elif "description" in result:
            st.write(result["description"])

        elif "text" in result:
            st.write(result["text"])

        else:
            st.write(result)

    else:
        st.error("Erreur API")