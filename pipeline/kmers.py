"""Métricas por secuencia y conteo de k-mers."""
import itertools

import numpy as np


def metricas(seq):
    """Longitud, contenido GC y conteo de N de una secuencia ya normalizada
    (mayúsculas; solo A, C, G, T y N).

    GC = (G + C) / (A + C + G + T) * 100. Las N no son ni GC ni AT, por eso
    quedan fuera del denominador. Lanza ValueError si no hay bases conocidas.
    """
    largo = len(seq)
    n = seq.count("N")
    conocidas = largo - n
    if conocidas == 0:
        raise ValueError("Secuencia sin bases conocidas: no se puede calcular el GC")
    gc = seq.count("G") + seq.count("C")
    return {
        "length": largo,
        "gc_content": gc / conocidas * 100,
        "n_count": n,
        "n_pct": n / largo * 100,
    }


# A=0, C=1, G=2, T=3, N=4, cualquier otro carácter=255 (inválido)
_CODIGOS = np.full(256, 255, dtype=np.uint8)
for _i, _b in enumerate("ACGT"):
    _CODIGOS[ord(_b)] = _i
_CODIGOS[ord("N")] = 4


def contar_kmers(seq, k):
    """Conteo de los k-mers de una secuencia normalizada (mayúsculas; A, C, G, T, N).

    Devuelve un arreglo de 4**k enteros en orden alfabético (AA, AC, AG, AT, CA, ...).
    Las ventanas que contienen N se saltan. Lanza ValueError ante cualquier
    otro carácter."""
    codigos = _CODIGOS[np.frombuffer(seq.encode("ascii"), dtype=np.uint8)]
    if (codigos == 255).any():
        raise ValueError("Caracteres no válidos: se esperan solo A, C, G, T y N en mayúsculas")

    n_vent = len(codigos) - k + 1
    if n_vent <= 0:
        return np.zeros(4 ** k, dtype=np.int64)

    es_n = codigos == 4
    bases = np.where(es_n, 0, codigos).astype(np.int64)

    # una ventana es válida si no contiene ninguna N (suma acumulada de N)
    acum = np.concatenate(([0], np.cumsum(es_n)))
    valida = (acum[k:] - acum[:-k]) == 0

    # cada ventana se codifica como un número en base 4 (el primer carácter pesa más)
    idx = np.zeros(n_vent, dtype=np.int64)
    for j in range(k):
        idx = idx * 4 + bases[j:j + n_vent]

    return np.bincount(idx[valida], minlength=4 ** k)


def kmers_todos(seq):
    """Diccionario {k: arreglo} para k = 1 a 6."""
    return {k: contar_kmers(seq, k) for k in range(1, 7)}


def etiquetas(k):
    """Los 4**k k-mers en el mismo orden que devuelve contar_kmers."""
    return ["".join(p) for p in itertools.product("ACGT", repeat=k)]