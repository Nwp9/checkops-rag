from prometheus_client import start_http_server
import time

# Démarre Prometheus sur le port 8000
from monitoring import registry
from prometheus_client import start_http_server

start_http_server(8000, registry=registry)

print("Prometheus server running on http://localhost:8000/metrics")

# Boucle infinie pour garder le serveur actif
while True:
    time.sleep(1)