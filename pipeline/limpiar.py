"""Funciones de limpieza compartidas por los notebooks del pipeline."""
import re
from pathlib import Path

import pandas as pd

ALFABETO_VALIDO = set("ACGTN")


COLS = ["Kingdom", "Phylum", "Class", "Order", "Family",
        "Species", "Source", "Source 2", "Notes"]

FUENTES_VALIDAS = {"Repbase", "Dfam"}

# Columnas de taxonomía de la especie (las que pueden traer marcadores de faltante)
TAXONOMIA = ["Kingdom", "Phylum", "Class", "Order", "Family"]

# Textos que el CSV usa para decir "no hay dato" ("No order", "No trobat", "No ordre NCBI"...).
# \b evita tocar nombres reales que empiezan por "No" (Nostocales, Noctuidae).
MARCADOR_FALTANTE = re.compile(r"(?i)^no\b")


def clave(s):
    """Clave de cruce: sin espacios en los extremos, minúsculas,
    sin puntos y con espacios internos colapsados.
    Debe usarse igual para el FASTA y el CSV."""
    s = s.strip().lower().replace(".", "")
    return re.sub(r"\s+", " ", s)


def limpiar_csv(ruta):
    """Lee el CSV de metadatos y devuelve las columnas del enunciado
    limpias, con Source 2 separada en source_2 y annotation, más la
    columna species_key para cruzar con el FASTA."""
    crudo = pd.read_csv(Path(ruta), dtype=str, keep_default_na=False)

    faltan = [c for c in COLS if c not in crudo.columns]
    assert not faltan, f"Columnas no encontradas: {faltan}"

    # Solo las 9 columnas, strip y vacío a None
    datos = crudo[COLS].copy()
    datos = datos.apply(lambda col: col.str.strip())
    datos = datos.replace("", None)
    datos = datos.astype(object).where(datos.notna(), None)

    # Marcadores de faltante en la taxonomía -> None (igual que un vacío)
    for col in TAXONOMIA:
        es_marcador = datos[col].fillna("").str.match(MARCADOR_FALTANTE)
        datos.loc[es_marcador, col] = None

    # Separar Source 2 en source_2 y annotation
    es_fuente = datos["Source 2"].isin(FUENTES_VALIDAS)
    tiene_valor = datos["Source 2"].notna()

    datos["source_2"] = datos["Source 2"].where(es_fuente, None)
    datos["annotation"] = datos["Source 2"].where(tiene_valor & ~es_fuente, None)
    datos = datos.drop(columns=["Source 2"])

    # Clave de cruce, sin tocar Species
    assert datos["Species"].notna().all(), "Species no debe tener vacíos"
    datos["species_key"] = datos["Species"].map(clave)

    return datos


def normalizar_secuencia(seq):
    """Pasa la secuencia a mayúsculas y verifica que solo contenga
    A, C, G, T y N. Devuelve la secuencia normalizada."""
    seq = seq.upper()
    invalidos = set(seq) - ALFABETO_VALIDO
    if invalidos:
        raise ValueError(f"Caracteres no válidos: {sorted(invalidos)}")
    return seq