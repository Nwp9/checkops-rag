import streamlit as st
from dotenv import load_dotenv
import re
import tempfile
import hashlib
from datetime import datetime
from core.generation import generate_answer
from services.ocr import ingest_ocr_pipeline

from corpus import (
    rag_query,
    detect_inconsistencies,
    compliance_score,
    search_documents,
    no_rag_answer,
    generate_pdf,
    extract_text_from_image
)

load_dotenv()

if "reset_input" not in st.session_state:
    st.session_state.reset_input = False

if st.session_state.reset_input:
    st.session_state.input_value = ""
    st.session_state.reset_input = False

# ==============================
# 🔹 SESSION STATE
# ==============================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ==============================
# 🔹 SESSION HISTORY
# ==============================

import json
import os

HISTORY_FILE = "history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception:
            return [] 
    return []

def save_history(history):
    
    # NE PAS écraser avec vide (sécurité)
    if history == []:
        return

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

if "history" not in st.session_state:
    st.session_state.history = load_history()

# Hidden History

HIDDEN_FILE = "hidden_history.json"

def load_hidden():
    if os.path.exists(HIDDEN_FILE):
        try:
            with open(HIDDEN_FILE, "r") as f:
                content = f.read().strip()
                if not content:
                    return []  # 🔥 fichier vide → liste vide
                return json.loads(content)
        except Exception:
            return []  # 🔥 fichier corrompu → reset propre
    return []


def save_hidden(hidden):
    with open(HIDDEN_FILE, "w") as f:
        json.dump(hidden, f, indent=2)

if "hidden_history" not in st.session_state:
    st.session_state.hidden_history = load_hidden()

# # ==============================
# # 🔐 USERS (HASH)
# # ==============================
# def hash_pwd(pwd):
#     return hashlib.sha256(pwd.encode()).hexdigest()

# USERS = {
#     "admin": {"password": hash_pwd("admin123"), "role": "admin"},
#     "engineer": {"password": hash_pwd("engineer123"), "role": "user"}
# }

# st.set_page_config(page_title="TechnOps Assistant", layout="wide", page_icon="🔩")

# # ==============================
# # 🔹 SESSION AUTH
# # ==============================
# if "authenticated" not in st.session_state:
#     st.session_state.authenticated = False
#     st.session_state.username = None

# # ==============================
# # 🔐 LOGIN
# # ==============================
# def login():

#     st.markdown("<h2 style='text-align:center;'>🔐 TechnOps</h2>", unsafe_allow_html=True)

#     col1, col2, col3 = st.columns([1,2,1])

#     with col2:
#         username = st.text_input("Username")
#         password = st.text_input("Password", type="password")

#         if st.button("Login"):
#             if username in USERS and USERS[username]["password"] == hash_pwd(password):
#                 st.session_state.authenticated = True
#                 st.session_state.username = username
#                 st.success("Connexion réussie")
#             else:
#                 st.error("Identifiants incorrects")

# # ==============================
# # 🔹 ROUTING AUTH
# # ==============================
# if not st.session_state.authenticated:
#     login()
#     st.stop()

# ==============================
# 🔹 SIDEBAR 
# ==============================
st.sidebar.title("⚙️ Configuration")

#st.sidebar.markdown(f"👤 {st.session_state.username}")

if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.stop()

mode = st.sidebar.radio(
    "Mode",
    [
        "Question (RAG)",
        "Question (Sans RAG)",
        "Analyse incohérences",
        "Score de conformité",
        "OCR (Vision)"
    ]
)

if "last_mode" not in st.session_state:
    st.session_state.last_mode = mode

if st.session_state.last_mode != mode:
    st.session_state.selected_history = None
    st.session_state.last_mode = mode

doc_type = st.sidebar.selectbox("Type", ["ALL", "AMM", "REPORT"])

st.sidebar.markdown("---")

visible_history = [
    h for h in st.session_state.history
    if h not in st.session_state.get("hidden_history", [])
]

st.sidebar.subheader("📜 Historique")

for i, item in enumerate(reversed(visible_history[-5:])):

    col1, col2 = st.sidebar.columns([4,1])

    label = item["query"] if isinstance(item, dict) else item

    with col1:
        if st.button(label, key=f"history_{i}"):
            if isinstance(item, dict):
                st.session_state.selected_history = item
            else:
                st.session_state.input_input = item["query]"]

        with col2:
            if st.button("❌", key=f"delete_{i}"):

                if "hidden_history" not in st.session_state:
                    st.session_state.hidden_history = []

                st.session_state.hidden_history.append(item)

                save_hidden(st.session_state.hidden_history)  # 🔥 IMPORTANT

                st.rerun()
                       

# ✅ EN DEHORS DE LA BOUCLE
st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Effacer tout l’historique", key="clear_history"):
    st.session_state.history = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("🔐 Données sensibles")

st.sidebar.markdown(
    "<p style='font-size:12px; color:#4A6FA5;'>Traitement conforme aux règles internes de confidentialité.</p>",
    unsafe_allow_html=True
)

# ==============================
# 🔹 UI CENTRÉE
# ==============================
st.markdown("""
<style>
.container {
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
    padding-top: 40px;
    text-align: center;
}
            
.card {
    background: rgb(43, 44, 54);
    padding: 40px;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 20px;
}
            
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="container">', unsafe_allow_html=True)

st.markdown(
    """
    <div class="card">
        <p style="
            color: rgb(250, 250, 250);
            font-size: 1.6rem;
            font-weight: 600;
            margin: 0;
            letter-spacing: 1px;
        ">
            Projet final : The AI on Azure !
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Image
st.markdown(
    "<div style='display:flex; justify-content:center;'>"
    "<img src='https://images.pexels.com/photos/25107261/pexels-photo-25107261.jpeg' width='400'>"
    "</div>",
    unsafe_allow_html=True
)

# Titre
st.markdown(
    "<h1 style='text-align:center;'>TechnOps Assistant</h1>"
    "<p style='text-align:center; font-size:25px; color:#4A6FA5;'>Maintenance • Analyse • IA</p>",
    unsafe_allow_html=True
)

# ==============================
# 🔹 MODE OCR
# ==============================
if mode == "OCR (Vision)":

    st.subheader("📷 Upload & Indexation OCR")

    uploaded_file = st.file_uploader("Upload image (PNG/JPG)", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded_file.read())
            temp_path = tmp.name

        if st.button("📥 Indexer l'image"):
            with st.spinner("Indexation en cours..."):

                nb_chunks = ingest_ocr_pipeline(temp_path)

            st.success(f"✅ Image indexée ({nb_chunks} chunks ajoutés)")
# ==============================
# 🔹 AUTRES MODES (RAG)
# ==============================
else:

    st.markdown("""
    <style>
    .search-box {
        display: flex;
        align-items: center;
        background-color: #0f172a;
        border: 1px solid #4A6FA5;
        border-radius: 30px;
        padding: 8px 15px;
        width: 550px;
    }
    .search-button {
        background-color: #4A6FA5;
        border: none;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================
# 💬 CHAT HISTORY DISPLAY
# ==============================

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for msg in st.session_state.chat_history:

    if msg["role"] == "user":
        st.markdown(f"""
        <div style="
            background-color:#1e293b;
            color:white;
            padding:12px;
            border-radius:10px;
            margin-bottom:10px;
            text-align:right;
        ">
        {msg["content"]}
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown(f"""
        <div style="
            background-color: rgb(250, 250, 250);
            color: rgb(4 40 112);
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 10px;
            text-align: left;
        ">
        {msg["content"]}
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# # ====================================================
# # La barre de recherche
# # ====================================================

st.markdown("---")  # séparation visuelle

with st.container():
    with st.form(key="search_form", clear_on_submit=False):

        col1, col2 = st.columns([4, 1])

        with col1:
            query = st.text_input(
                "",
                placeholder="Rechercher dans TechnOps...",
                key="input_value",
                label_visibility="collapsed"
            )

        with col2:
            run = st.form_submit_button("Analyser")

# Affichage historique sélectionné 

if st.session_state.get("selected_history") and not (run and query):

    st.markdown("### 📜 Détail de la recherche")

    st.markdown(
        f"**Question :** {st.session_state.selected_history['query']}"
    )

    st.markdown(f"""
    <div style="
        background-color:#163d2b;
        color:#b9fbc0;
        padding:20px;
        border-radius:12px;
        font-size:16px;
        margin-bottom:20px;
    ">
    {st.session_state.selected_history['answer']}
    </div>
    """, unsafe_allow_html=True)

if run and query:
    st.session_state.selected_history = None

    # USER MESSAGE
    st.session_state.chat_history.append({
        "role": "user",
        "content": query
    })
                                         
    with st.spinner("Analyse en cours..."):

        selected_type = None if doc_type == "ALL" else doc_type
        
        from corpus import evaluate_rag

        if mode == "Question (RAG)":
            answer, docs = rag_query(query, doc_type=selected_type)
            score = evaluate_rag(answer, docs)
            st.caption(f"📊 Score RAG : {score}/100")
                                
        elif mode == "Question (Sans RAG)":
            answer = no_rag_answer(query)
            docs = []

        elif mode == "Analyse incohérences":
            answer = detect_inconsistencies(query)
            docs = search_documents(query, doc_type=selected_type)

        else:
            answer = compliance_score(query)
            docs = search_documents(query, doc_type=selected_type)
    st.session_state.history.append({
        "query": query,
        "answer": answer
    })

    # ASSISTANT MESSAGE
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer
    })

    st.session_state.reset_input = True
    st.rerun()

    save_history(st.session_state.history)
              
    pdf_file = generate_pdf(query, answer, docs)

    # Nettoyage du nom de fichier
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', query)[:50]

    with open(pdf_file, "rb") as f:
        st.download_button(
            label="📄 Télécharger PDF",
            data=f,
            file_name=f"{safe_name}.pdf",
            mime="application/pdf"
        )
                        
    if docs:
        with st.expander("📄 Sources"):
            for d in docs:
                st.write(d["content"][:200])

st.markdown('</div>', unsafe_allow_html=True)