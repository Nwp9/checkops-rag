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

# ==============================
# 🔹 SESSION STATE
# ==============================
if "reset_input" not in st.session_state:
    st.session_state.reset_input = False

if st.session_state.reset_input:
    st.session_state.input_value = ""
    st.session_state.reset_input = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_graph" not in st.session_state:
    st.session_state.last_graph = None

# ==============================
# 🔐 USERS (HASH)
# ==============================
# def hash_pwd(pwd):
#     return hashlib.sha256(pwd.encode()).hexdigest()

# USERS = {
#     "admin": {"password": hash_pwd("admin123"), "role": "admin"},
#     "engineer": {"password": hash_pwd("engineer123"), "role": "user"},
#     "stagiaire": {"password": hash_pwd("stage123"), "role": "user"}
# }

# st.set_page_config(page_title="CheckOps", layout="wide", page_icon="🔩")

# ==============================
# 🔹 SESSION AUTH
# ==============================
# if "authenticated" not in st.session_state:
#     st.session_state.authenticated = False
#     st.session_state.username = None

# ==============================
# 🔐 LOGIN
# ==============================
# def login():

#     st.markdown("<h2 style='text-align:center;'>🔐 CheckOps</h2>", unsafe_allow_html=True)

#     col1, col2, col3 = st.columns([1, 2, 1])

#     with col2:
#         with st.form("login_form"):
#             username = st.text_input("Username")
#             password = st.text_input("Password", type="password")

#             submitted = st.form_submit_button("Login")

#             if submitted:
#                 if username in USERS and USERS[username]["password"] == hash_pwd(password):
#                     st.session_state.authenticated = True
#                     st.session_state.username = username
#                     st.success("Connexion réussie")
#                     st.rerun()
#                 else:
#                     st.error("Identifiants incorrects")

# ==============================
# ROUTING AUTH
# ==============================
# if not st.session_state.authenticated:
#     login()
#     st.stop()

# ==============================
# 🔹 SIDEBAR
# ==============================

st.sidebar.markdown("""
<style>
.sidebar-logo {
    font-size: 28px;
    font-weight: 800;
    margin-bottom: 35px;
}

.sidebar-logo .check {
    color: #7C7CFF;
}

.sidebar-logo .ops {
    color: #FFFFFF;
}

.sidebar-section {
    margin-top: 20px;
}

.sidebar-info {
    font-size: 13px;
    color: #94A3B8;
}
                    
/* STYLE MENU CLEAN */
div[data-testid="stSidebar"] button {
    justify-content: flex-start !important;
    text-align: left !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    font-weight: 600 !important;
}

/* boutons non actifs */
div[data-testid="stSidebar"] button[kind="secondary"] {
    background-color: transparent !important;
    color: #cbd5e1 !important;
}

/* bouton actif */
div[data-testid="stSidebar"] button[kind="primary"] {
    background: linear-gradient(90deg, #4f46e5, #3730a3) !important;
    color: white !important;
}

/* hover */
div[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background-color: #202436 !important;
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

st.sidebar.markdown(
    """
    <div class="sidebar-logo">
        <span class="check">Check</span><span class="ops">Ops</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

# ==============================
# 🔹 MENU
# ==============================

if "mode_ui" not in st.session_state:
    st.session_state.mode_ui = "Assistant RAG"

def nav_item(label, value, key):
    active = st.session_state.mode_ui == value

    if st.sidebar.button(
        label,
        key=key,
        use_container_width=True,
        type="primary" if active else "secondary"
    ):
        st.session_state.mode_ui = value
        st.rerun()

nav_item("Accueil", "Accueil", "nav_accueil")
nav_item("Assistant RAG", "Assistant RAG", "nav_rag")
nav_item("Assistant Sans RAG", "Assistant Sans RAG", "nav_no_rag")
nav_item("Ingestion", "Ingestion", "nav_ingestion")
nav_item("Monitoring", "Monitoring", "nav_monitoring")

mode = st.session_state.mode_ui

if "last_mode" not in st.session_state:
    st.session_state.last_mode = mode

if st.session_state.last_mode != mode:
    st.session_state.chat_history = []
    st.session_state.last_score = None
    st.session_state.input_value = ""
    st.session_state.last_mode = mode
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("🔐 Données sensibles")

st.sidebar.markdown(
    "<p style='font-size:12px; color:#4A6FA5;'>Traitement conforme aux règles internes de confidentialité.</p>",
    unsafe_allow_html=True
)

# ==============================
# 🔹 FOOTER SIDEBAR (BAS)
# ==============================

st.sidebar.markdown(
    """
    <style>
    .sidebar-footer {
        position: fixed;
        bottom: 20px;
        left: 20px;
        width: 220px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown('<div class="sidebar-footer">', unsafe_allow_html=True)

# User
# st.sidebar.markdown(f"👤 {st.session_state.username}")

# Logout
if "confirm_logout" not in st.session_state:
    st.session_state.confirm_logout = False

if st.sidebar.button("Logout"):
    st.session_state.confirm_logout = True

if st.session_state.confirm_logout:
    st.sidebar.warning("Confirmer la fermeture de session utilisateur ?")

    col_logout_1, col_logout_2 = st.sidebar.columns(2)

    with col_logout_1:
        if st.button("Oui", key="confirm_logout_yes"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.confirm_logout = False
            st.rerun()

    with col_logout_2:
        if st.button("Non", key="confirm_logout_no"):
            st.session_state.confirm_logout = False
            st.rerun()


st.sidebar.markdown('</div>', unsafe_allow_html=True)

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

[data-testid="stFileUploaderDropzone"] {
    background-color: #41488C !important;
    border-radius: 0.5rem;
    padding: 1rem;
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

st.markdown(
    """
    <div style="display:flex; justify-content:center; margin-top:20px;">
        <img src="https://images.pexels.com/photos/13687210/pexels-photo-13687210.png"
             style="width:600px; border-radius:15px; box-shadow:0px 10px 30px rgba(0,0,0,0.5);">
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <h1 style='text-align:center; font-size:48px; font-weight:800; margin-bottom:10px;'>
        <span style='color:#7C7CFF;'>Check</span><span style='color:#FFFFFF;'>Ops</span>
    </h1>
    <p style='text-align:center; font-size:25px; color:#4A6FA5;'>
        Maintenance • Analyse • IA
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# ==============================
# 🔹 MODE INGESTION UNIQUE
# ==============================
if mode == "Ingestion":

    st.subheader("📥 Upload & Indexation")

    from core.vector_store import clear_collection

    if st.button("Vider l'index"):
        with st.spinner("Suppression en cours..."):
            clear_collection()
        st.success("Index vidé")

    ingestion_type = st.radio(
        "Type d'ingestion",
        [
            "Document classique",
            "OCR",
            "Dessin industriel"
        ],
        horizontal=True
    )

    if ingestion_type == "Document classique":

        uploaded_file = st.file_uploader(
            "Upload document (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"]
        )

        if uploaded_file:

            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(uploaded_file.read())
                temp_path = tmp.name

            if st.button("📄 Indexer le document"):

                with st.spinner("Indexation du document en cours..."):

                    from core.indexing import index_chunks

                    file_type = uploaded_file.name.split(".")[-1].lower()
                    chunks = ingest_document(temp_path, file_type)
                    index_chunks(chunks)
                    nb_chunks = len(chunks)

                if nb_chunks > 0:
                    st.success(f"✅ Document indexé ({nb_chunks} chunks)")

    elif ingestion_type == "OCR":

        uploaded_file = st.file_uploader(
            "Upload image(PNG, JPG, JPEG)",
            type=["png", "jpg", "jpeg"]
        )

        if uploaded_file:
            st.info("Image chargée. Prête pour l'OCR.")

            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(uploaded_file.read())
                temp_path = tmp.name

            if st.button("🖼️ Extraire et indexer le texte"):

                with st.spinner("OCR et indexation en cours..."):
                    nb_chunks = ingest_ocr_pipeline(temp_path)

                if nb_chunks > 0:
                    st.success(f"✅ Image OCR indexée ({nb_chunks} chunks)")
                else:
                    st.warning("Aucun texte exploitable détecté.")

    elif ingestion_type == "Dessin industriel":

        uploaded_file = st.file_uploader(
            "Upload dessin industriel (PNG, JPG, JPEG)",
            type=["png", "jpg", "jpeg"]
        )

        if uploaded_file:
            st.info("Image chargée. Prête pour l’analyse industrielle.")

            from services.drawing_analysis import (
                analyze_industrial_drawing,
                build_chunks_from_drawing_analysis
            )
            from core.indexing import index_chunks
            from services.graph_builder import (
                build_simple_graph_from_text,
                graph_to_text,
                build_graph_chunks,
                save_graph_image
            )

            if st.button("🏭 Analyser et indexer le dessin"):

                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(uploaded_file.read())
                    temp_path = tmp.name

                with st.spinner("Analyse du dessin en cours..."):

                    analysis = analyze_industrial_drawing(temp_path)

                    G = build_simple_graph_from_text(analysis)
                    graph_text = graph_to_text(G)

                    st.session_state.last_graph = G

                    graph_image_path = save_graph_image(G)

                    graph_chunks = build_graph_chunks(
                        graph_text,
                        uploaded_file.name
                    )

                    chunks = build_chunks_from_drawing_analysis(
                        analysis,
                        uploaded_file.name
                    )

                    index_chunks(chunks + graph_chunks)

                st.success("✅ Dessin analysé et indexé avec succès")

                if graph_image_path:
                    st.image(graph_image_path, caption="Graphe technique extrait")

# ==============================
# 🔹 MODE MONITORING
# ==============================
elif mode == "Monitoring":

    st.subheader("Monitoring")

    st.markdown("Accès aux outils de supervision :")

    st.link_button("Ouvrir Prometheus", "http://localhost:9090")
    st.link_button("Ouvrir Grafana", "http://localhost:3000")

    st.info("Prometheus et Grafana doivent déjà être lancés.")

# ==============================
# 🔹 MODES QUESTION
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

            if msg.get("sources"):
                with st.expander("Sources utilisées"):
                    for d in msg["sources"]:
                        source_type = d.get("type", "DOC")

                        if source_type == "DRAWING":
                            label = "🔧 Dessin industriel"
                        elif source_type == "GRAPH":
                            label = "🧠 Graphe technique"
                        elif source_type == "OCR":
                            label = "🖼️ OCR"
                        else:
                            label = "📄 Document"

                        st.markdown(f"**{label} - {d.get('title', 'Document')}**")
                        st.write(d["content"][:200])

            if msg.get("score") is not None:
                score = msg.get("score")

                if score >= 75:
                    level = "🟢 Élevé"
                elif score >= 50:
                    level = "🟡 Moyen"
                else:
                    level = "🔴 Faible"

                st.caption(f"Score : {score}/100 — Confiance : {level}")

    st.markdown('</div>', unsafe_allow_html=True)

    # ==============================
    # BARRE DE RECHERCHE
    # ==============================

    st.markdown("---")
    st.markdown("""
    <style>
    .chat-input-wrapper {
        background: transparent;
        border: none;
        padding: 0;
        margin-top: 25px;
    }

    /* supprime le cadre natif du formulaire Streamlit */
    div[data-testid="stForm"] {
        border: none !important;
        background: #151827 !important;
        border-radius: 18px !important;
        padding: 12px !important;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.25) !important;
    }       
   
    /* Input */
    div[data-testid="stTextInput"] input {
        background-color: #202436 !important;
        color: white !important;
        border-radius: 12px !important;
        border: 1px solid #343a55 !important;
        padding: 12px !important;
        height: 48px !important;
    }

    /* Bouton */
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(90deg, #4f46e5, #3730a3) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        height: 48px !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="chat-input-wrapper">', unsafe_allow_html=True)

    with st.form(key="search_form", clear_on_submit=False):

        col1, col2 = st.columns([6, 1], gap="small")

        with col1:
            query = st.text_input(
                "",
                placeholder="Posez votre question sur la documentation technique...",
                key="input_value",
                label_visibility="collapsed"
            )

        with col2:
            run = st.form_submit_button("Envoyer")

    st.markdown('</div>', unsafe_allow_html=True)

    # with st.container():
    #     with st.form(key="search_form", clear_on_submit=False):

    #         col1, col2 = st.columns([4, 1])

    #         with col1:
    #             query = st.text_input(
    #                 "",
    #                 placeholder="CheckOps — votre question de maintenance…",
    #                 key="input_value",
    #                 label_visibility="collapsed"
    #             )

    #         with col2:
    #             run = st.form_submit_button("Analyser")

    if run and query:

        graph_query_handled = False

        if st.session_state.get("last_graph") is not None:
            from services.graph_builder import find_path_between_components, get_direct_neighbors

            match_path = re.search(r"chemin entre (.+) et (.+)", query.lower())
            match_neighbors = re.search(
                r"(?:connectés|connectees|reliés|relies|liés|lies) (?:au|à la|à l'|a la|a l'|à|a) (.+)",
                query.lower()
            )

            if match_path:
                source = match_path.group(1).strip()
                target = match_path.group(2).strip()
                answer = find_path_between_components(st.session_state.last_graph, source, target)
                docs = []
                score = None
                graph_query_handled = True

            elif match_neighbors:
                component = match_neighbors.group(1).strip()
                answer = get_direct_neighbors(st.session_state.last_graph, component)
                docs = []
                score = None
                graph_query_handled = True

        st.session_state.chat_history.append({
            "role": "user",
            "content": query
        })

        if not graph_query_handled:
            with st.spinner("Analyse en cours..."):

                from corpus import evaluate_rag

                if mode == "Assistant RAG":
                
                    answer, docs = rag_query(query)
                    score = evaluate_rag(query, docs)
                    st.session_state.last_score = score
                
                elif mode == "Assistant Sans RAG":

                    answer = no_rag_answer(query)
                    docs = []
                    score = None

                else:
                    answer = compliance_score(query)
                    docs = search_documents(query)
                    score = None

        else:
            st.session_state.last_score = score

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": answer,
            "score": score,
            "sources": docs
        })

        pdf_file = generate_pdf(query, answer, docs)

        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', query)[:50]

        with open(pdf_file, "rb") as f:
            st.session_state.last_pdf = f.read()
            st.session_state.last_pdf_name = f"{safe_name}.pdf"

        st.session_state.reset_input = True
        st.rerun()

    if "last_pdf" in st.session_state:
        st.download_button(
            label="📄 Télécharger PDF",
            data=st.session_state.last_pdf,
            file_name=st.session_state.last_pdf_name,
            mime="application/pdf"
        )

st.markdown('</div>', unsafe_allow_html=True)