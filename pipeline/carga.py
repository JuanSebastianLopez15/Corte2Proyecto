"""Armado de documentos y carga por lotes a MongoDB."""
import numpy as np
from pipeline.fasta import leer_fasta

from pymongo.errors import BulkWriteError
import time
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


def cargar_lotes(coleccion, documentos, campo_id, tam=1000, cada=10):
    """Inserta por lotes de 'tam' documentos desde cualquier iterable (también
    un generador). Imprime el progreso cada 'cada' lotes (0 = en silencio).
    Devuelve (insertados, rechazados), donde rechazados es una lista de
    (valor de campo_id, código de error)."""
    insertados, rechazados, lote, n_lotes = 0, [], [], 0
    t0 = time.perf_counter()

    def volcar():
        nonlocal insertados, n_lotes
        n, errores = _insertar(coleccion, lote)
        insertados += n
        rechazados.extend((lote[e["index"]].get(campo_id), e["code"]) for e in errores)
        n_lotes += 1
        if cada and n_lotes % cada == 0:
            t = time.perf_counter() - t0
            print(f"  {insertados:>8,} insertados | {len(rechazados)} rechazados | {t/60:.1f} min")

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

def secuencias_pendientes(db, ruta_fasta, especies=None):
    """Genera los documentos de 'sequences' que aún no están en MongoDB
    (así el pipeline se puede reanudar sin duplicar ni recalcular)."""
    ya = set(db.sequences.distinct("sequence_id"))
    for campos in leer_fasta(ruta_fasta, especies):
        if campos["sequence_id"] not in ya:
            yield armar_secuencia(campos)