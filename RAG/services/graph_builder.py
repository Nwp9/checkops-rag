import json
import os
import re

import networkx as nx
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

chat_model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")


ALLOWED_RELATIONS = {
    "fixe",
    "supporte",
    "entraîne",
    "guide",
    "protège",
    "alimente",
    "contrôle",
    "est relié à"
}


def _extract_json_from_response(raw_text):
    """
    Sécurise le parsing JSON si le modèle retourne du texte autour du JSON.
    """
    if not raw_text:
        return {"components": [], "relations": []}

    raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return {"components": [], "relations": []}


def extract_graph_data_with_llm(analysis_text):
    """
    Extrait dynamiquement les composants et relations techniques
    depuis l'analyse textuelle d'un dessin industriel.
    """

    prompt = f"""
Tu analyses un texte issu d'un dessin industriel.

Objectif :
Extraire les composants techniques et leurs relations.

Retourne uniquement un JSON valide au format suivant :
{{
  "components": ["composant 1", "composant 2"],
  "relations": [
    {{
      "from": "composant 1",
      "to": "composant 2",
      "relation": "fixe | supporte | entraîne | guide | protège | alimente | contrôle | est relié à"
    }}
  ]
}}

Règles :
- N'invente aucun composant.
- Utilise uniquement les éléments présents dans le texte.
- Choisis la relation la plus précise possible parmi : fixe, supporte, entraîne, guide, protège, alimente, contrôle, est relié à.
- Si aucune relation précise n’est identifiable, utilise "est relié à".
- Si aucune relation explicite n'est trouvée, utilise seulement les relations mécaniques probables décrites dans le texte.
- Évite les doublons dans les composants et les relations.
- Ne retourne aucun commentaire hors JSON.

Texte :
{analysis_text}
"""

    try:
        response = client.chat.completions.create(
            model=chat_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert en extraction de graphes techniques industriels. "
                        "Tu retournes uniquement du JSON valide."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        raw = response.choices[0].message.content
        graph_data = _extract_json_from_response(raw)

        return {
            "components": graph_data.get("components", []),
            "relations": graph_data.get("relations", [])
        }

    except Exception:
        return {
            "components": [],
            "relations": []
        }


def build_simple_graph_from_text(analysis_text):
    """
    Construction dynamique du graphe à partir de l'analyse du dessin.
    Les composants et relations sont extraits par LLM.
    """

    G = nx.Graph()

    graph_data = extract_graph_data_with_llm(analysis_text)

    components = graph_data.get("components", [])
    relations = graph_data.get("relations", [])

    # Ajout des composants comme nœuds
    for component in components:
        if isinstance(component, str) and component.strip():
            G.add_node(component.strip())

    # Ajout des relations comme arêtes
    for relation in relations:
        if not isinstance(relation, dict):
            continue

        source = relation.get("from")
        target = relation.get("to")
        label = relation.get("relation", "est relié à")

        if not source or not target:
            continue

        source = str(source).strip()
        target = str(target).strip()
        label = str(label).strip()

        if label not in ALLOWED_RELATIONS:
            label = "est relié à"

        if source and target and source != target:
            G.add_node(source)
            G.add_node(target)
            G.add_edge(source, target, relation=label)

    return G


def graph_to_text(G):
    """
    Transforme le graphe NetworkX en texte exploitable par le RAG.
    """

    if len(G.nodes) == 0:
        return "Aucun composant identifié dans le graphe."

    lines = ["Graphe technique détecté :"]

    for node in G.nodes:
        neighbors = list(G.neighbors(node))

        if neighbors:
            relations = []

            for neighbor in neighbors:
                relation = G.edges[node, neighbor].get("relation", "est relié à")
                relations.append(f"{relation} {neighbor}")

            lines.append(f"- {node} : {', '.join(relations)}")
        else:
            lines.append(f"- {node} (isolé)")

    return "\n".join(lines)


def build_graph_chunks(graph_text, filename):
    """
    Prépare le graphe sous forme de chunk indexable dans ChromaDB.
    """

    return [
        {
            "title": filename,
            "content": graph_text,
            "source": filename,
            "type": "GRAPH",
            "section": "technical_graph"
        }
    ]

def save_graph_image(G, output_path="graph.png"):
    import matplotlib.pyplot as plt

    if len(G.nodes) == 0:
        return None

    plt.figure(figsize=(8, 6))

    pos = nx.spring_layout(G, seed=42)

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=2500,
        font_size=9,
        edgecolors="black"
    )

    edge_labels = nx.get_edge_attributes(G, "relation")
    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_labels,
        font_size=8
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path

def find_path_between_components(G, source, target):
    try:
        path = nx.shortest_path(G, source=source, target=target)
        return " → ".join(path)
    except nx.NetworkXNoPath:
        return f"Aucun chemin trouvé entre {source} et {target}."
    except nx.NodeNotFound:
        return f"Composant introuvable dans le graphe."

def get_direct_neighbors(G, component):
    if component not in G.nodes:
        return f"Composant introuvable : {component}"

    neighbors = list(G.neighbors(component))

    if not neighbors:
        return f"{component} n’a aucune connexion directe."

    return f"{component} est directement connecté à : {', '.join(neighbors)}"