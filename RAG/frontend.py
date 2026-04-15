import streamlit as st
from dotenv import load_dotenv
import re
import tempfile
import hashlib
from datetime import datetime
from core.generation import generate_answer
from services.ocr import ingest_ocr_pipeline

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from prometheus_client import start_http_server

if "prometheus_started" not in st.session_state:
    start_http_server(8000)
    st.session_state.prometheus_started = True

from corpus import (
    rag_query,
    detect_inconsistencies,
    compliance_score,
    search_documents,
    no_rag_answer,
    generate_pdf,
    extract_text_from_image,
    ingest_document
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

# # ==============================
# # 🔐 USERS (HASH)
# # ==============================
# def hash_pwd(pwd):
#     return hashlib.sha256(pwd.encode()).hexdigest()

# USERS = {
#     "admin": {"password": hash_pwd("admin123"), "role": "admin"},
#     "engineer": {"password": hash_pwd("engineer123"), "role": "user"},
#     "stagiaire": {"password": hash_pwd("stage123"), "role": "user"}
# }

# st.set_page_config(page_title="CheckOps", layout="wide", page_icon="🔩")

# # # ==============================
# # # 🔹 SESSION AUTH
# # # ==============================
# if "authenticated" not in st.session_state:
#     st.session_state.authenticated = False
#     st.session_state.username = None

# # # ==============================
# # # 🔐 LOGIN
# # # ==============================
# def login():

#     st.markdown("<h2 style='text-align:center;'>🔐 CheckOps</h2>", unsafe_allow_html=True)

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

# # # ==============================
# # #  ROUTING AUTH
# # # ==============================
# if not st.session_state.authenticated:
#     login()
#     st.stop()

# ==============================
# 🔹 SIDEBAR 
# ==============================
st.sidebar.title("⚙️ Configuration")

# st.sidebar.markdown(f"👤 {st.session_state.username}")

if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.stop()

mode = st.sidebar.radio(
    "Mode",
    [
        "Question (RAG)",
        "Question (Sans RAG)",
        "Ingestion 📥"
        
    ]
)

if "last_mode" not in st.session_state:
    st.session_state.last_mode = mode

if st.session_state.last_mode != mode:
    # reset complet UI
    st.session_state.chat_history = []
    st.session_state.last_score = None
    st.session_state.input_value = ""

    st.session_state.last_mode = mode

    st.rerun()

st.sidebar.markdown("---")

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
            E5 MBA Data - PLG Projet Pédagogique
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Image
st.markdown(
    "<div style='display:flex; justify-content:center;'>"
    "<img src='https://images.pexels.com/photos/13687210/pexels-photo-13687210.png' width='600'>"
    "</div>",
    unsafe_allow_html=True
)

# Titre
st.markdown(
    "<h1 style='text-align:center;'>CheckOps</h1>"
    "<p style='text-align:center; font-size:25px; color:#4A6FA5;'>Maintenance • Analyse • IA</p>",
    unsafe_allow_html=True
)

# ==============================
# 🔹Ingestion des documents
# ==============================
if mode == "Ingestion 📥":

    st.subheader("📥 Upload & Indexation")

    from core.vector_store import clear_collection

    if st.button("Vider l'index"):
        with st.spinner("Suppression en cours..."):
            clear_collection()
        st.success("Index vidé")
    
    uploaded_file = st.file_uploader(
        "Upload fichier (Image, PDF, DOCX, TXT)",
        type=["png", "jpg", "jpeg", "pdf", "docx", "txt"]
    )

    if uploaded_file:

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded_file.read())
            temp_path = tmp.name

        if st.button("📥 Indexer le document"):

            with st.spinner("Indexation en cours..."):

                file_type = uploaded_file.name.split(".")[-1].lower()

                # ROUTING
                if file_type in ["png", "jpg", "jpeg"]:
                    nb_chunks = ingest_ocr_pipeline(temp_path)

                else:  
                    from core.indexing import index_chunks        
                    filename = uploaded_file.name.lower().strip() 

                    chunks = ingest_document(temp_path, file_type)
                    index_chunks(chunks)
                    nb_chunks = len(chunks)               

            if nb_chunks > 0:
                st.success(f"✅ Document indexé ({nb_chunks} chunks)")
            

    st.markdown("""
    <style>
    [data-testid="stFileUploaderDropzone"] {
        background-color: #41488C !important;  /* ta couleur */
        border-radius: 0.5rem;
        padding: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

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
# CHAT HISTORY DISPLAY
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
            font-weight:500;
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
            margin-bottom: 5px;
            text-align: left;
        ">
        {msg["content"]}
        </div>
        """, unsafe_allow_html=True)
    
    # affichage des sources
        if msg.get("sources"):
            with st.expander("Sources utilisées"):
                for d in msg["sources"]:
                    st.markdown(f"**📄 {d.get('title', 'Document')}**")
                    st.write(d["content"][:200])

        # affichage score par message
        if msg.get("score") is not None:
            st.caption(f"Score de pertinence : {msg['score']}/100")
            

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
                placeholder="CheckOps — votre question de maintenance…",
                key="input_value",
                label_visibility="collapsed"
            )

        with col2:
            run = st.form_submit_button("Analyser")


if run and query:
   
    # USER MESSAGE
    st.session_state.chat_history.append({
        "role": "user",
        "content": query
    })
                                         
    with st.spinner("Analyse en cours..."):

        selected_type = None
        
        from corpus import evaluate_rag

        if mode == "Question (RAG)":
            answer, docs = rag_query(query)
            score = evaluate_rag(query, docs)
            st.session_state.last_score = score
                              
        elif mode == "Question (Sans RAG)":
            answer = no_rag_answer(query)
            docs = []

        elif mode == "Analyse incohérences":
            answer = detect_inconsistencies(query)
            docs = search_documents(query)

        else:
            answer = compliance_score(query)
            docs = search_documents(query)

    # ASSISTANT MESSAGE

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer,
        "score": st.session_state.get("last_score"),
        "sources": docs
    })

# Généréation du fichier pdf de la conversation

    pdf_file = generate_pdf(query, answer, docs)

    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', query)[:50]

    with open(pdf_file, "rb") as f:
        st.session_state.last_pdf = f.read()
        st.session_state.last_pdf_name = f"{safe_name}.pdf"
    
    
    st.session_state.reset_input = True
    st.rerun()  
                       
    if docs:
        with st.expander("📄 Sources"):
            for d in docs:
                st.markdown(f"**📄 {d.get('title', 'Document')}**")
                st.write(d["content"][:200])

st.markdown('</div>', unsafe_allow_html=True)

# affichage persistant du PDF
if "last_pdf" in st.session_state:
    st.download_button(
        label="📄 Télécharger PDF",
        data=st.session_state.last_pdf,
        file_name=st.session_state.last_pdf_name,
        mime="application/pdf"
    )
