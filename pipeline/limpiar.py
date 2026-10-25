
import re
from pathlib import Path

import pandas as pd

COLS = ["Kingdom", "Phylum", "Class", "Order", "Family",
        "Species", "Source", "Source 2", "Notes"]


def clave(s):
    #sin espacios en los extremos, minúsculas,
    
    #sin puntos y con espacios internos colapsados.
    #Debe usarse igual para el FASTA y el CSV."""
    s = s.strip().lower().replace(".", "")
    return re.sub(r"\s+", " ", s)


def limpiar_csv(ruta):
   # Lee el CSV de metadatos y devuelve las 9 columnas del enunciado
  #  limpias, más la columna species_key para cruzar con el FASTA."""
    crudo = pd.read_csv(Path(ruta), dtype=str, keep_default_na=False)

    faltan = [c for c in COLS if c not in crudo.columns]
    assert not faltan, f"Columnas no encontradas: {faltan}"

    # Paso 1 y 2: 9 columnas, strip y vacíos a None real
    datos = crudo[COLS].copy()
    datos = datos.apply(lambda col: col.str.strip())
    datos = datos.replace("", None)
    datos = datos.astype(object).where(datos.notna(), None)

    # Paso 3: clave de cruce, sin tocar Species
    assert datos["Species"].notna().all(), "Species no debe tener vacíos"
    datos["species_key"] = datos["Species"].map(clave)

    return datos