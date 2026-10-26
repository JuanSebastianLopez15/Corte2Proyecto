"""Armado de documentos y carga por lotes a MongoDB."""
import numpy as np
from pymongo.errors import BulkWriteError

from pipeline.kmers import contar_kmers, etiquetas, metricas

# Las etiquetas se calculan una sola vez (5.460 textos en total)
_ETIQ = {k: etiquetas(k) for k in range(1, 7)}


def kmers_a_dict(seq):
    """{'k1': {'A': 2, ...}, ..., 'k6': {...}}: solo los k-mers presentes,
    con enteros nativos de Python."""
    salida = {}
    for k in range(1, 7):
        arr = contar_kmers(seq, k)
        et = _ETIQ[k]
        salida[f"k{k}"] = {et[i]: int(arr[i]) for i in np.flatnonzero(arr)}
    return salida


def armar_secuencia(campos):
    """Documento de la colección 'sequences' a partir de un registro de leer_fasta."""
    seq = campos["sequence"]
    m = metricas(seq)
    return {
        "sequence_id": campos["sequence_id"],
        "species_key": campos["species_key"],
        "species_raw": campos["species_raw"],
        "te_class": campos["te_class"],
        "te_order": campos["te_order"],
        "te_superfamily": campos["te_superfamily"],
        "classification_raw": campos["classification_raw"],
        "sequence": seq,
        "metrics": {
            "length": int(m["length"]),
            "gc_content": float(m["gc_content"]),
            "n_count": int(m["n_count"]),
            "n_pct": float(m["n_pct"]),
        },
        "kmers": kmers_a_dict(seq),
    }


def armar_especies(tabla, claves):
    """Documentos de la colección 'species' a partir del CSV limpio
    (los vacíos ya son None, que MongoDB guarda como null)."""
    return tabla[tabla["species_key"].isin(claves)].to_dict("records")


def _insertar(coleccion, lote):
    try:
        res = coleccion.insert_many(lote, ordered=False)
        return len(res.inserted_ids), []
    except BulkWriteError as e:
        return e.details["nInserted"], e.details["writeErrors"]


def cargar_lotes(coleccion, documentos, campo_id, tam=1000):
    """Inserta por lotes de 'tam' documentos desde cualquier iterable (también
    un generador). Devuelve (insertados, rechazados), donde rechazados es una
    lista de (valor de campo_id, código de error)."""
    insertados, rechazados, lote = 0, [], []

    def volcar():
        nonlocal insertados
        n, errores = _insertar(coleccion, lote)
        insertados += n
        rechazados.extend((lote[e["index"]].get(campo_id), e["code"]) for e in errores)

    for doc in documentos:
        lote.append(doc)
        if len(lote) >= tam:
            volcar()
            lote = []
    if lote:
        volcar()
    return insertados, rechazados

def cargar_species(db, tabla):
    """Carga TODAS las especies del CSV limpio en db.species.
    Devuelve (insertadas, rechazadas), igual que cargar_lotes."""
    docs = armar_especies(tabla, set(tabla["species_key"]))
    return cargar_lotes(db.species, docs, "species_key")