import os
import logging
from . import utils, config, logger
import pandas as pd
import requests

log = logging.getLogger(__name__)

def load(log_queue):
    logger.setup_worker_logger(log_queue)

    if not utils.if_active("tabula"):
        return

    # 1. RAW-URL des JSON-Files
    url = "https://raw.githubusercontent.com/RWTH-EBC/TEASER/main/teaser/data/input/inputdata/TypeElements_TABULA_DE.json"

    # 2. JSON herunterladen
    response = requests.get(url)
    response.raise_for_status()  # Fehlerbehandlung

    # 3. In Python-Datenstruktur umwandeln
    json_data = response.json()

    # 4. Optional: In Pandas DataFrame umwandeln
    # Beispiel: obere Ebene ist ein Dict mit Gebäudetypen → flattenen je nach Struktur
    df = pd.json_normalize(json_data)

    # Ausgabe
    print(df.head())

    log.info(f"TABULA data loaded successfully")