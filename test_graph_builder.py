import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "RAG"))

from services.graph_builder import build_simple_graph_from_text, graph_to_text

analysis_text = """
Le schéma montre un moteur commandé par un relais.
Un fusible protège le circuit.
Un capteur permet de contrôler l’état du système.
"""

G = build_simple_graph_from_text(analysis_text)

print(graph_to_text(G))