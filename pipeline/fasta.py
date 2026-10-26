"""Lectura del FASTA en streaming: un registro a la vez, sin cargar el archivo en memoria."""
from Bio import SeqIO

from pipeline.limpiar import clave, normalizar_secuencia


def separar_encabezado(descripcion):
    """Separa 'ID#CLASE/ORDEN/SUPERFAMILIA @Especie' en sus partes.
    Lanza ValueError si falta '#' o '@', o si no hay tres niveles."""
    if "#" not in descripcion or "@" not in descripcion:
        raise ValueError(f"Encabezado mal formado: {descripcion!r}")

    id_, resto = descripcion.split("#", 1)
    clasif, especie = resto.split("@", 1)
    clasif = clasif.strip()
    niveles = [n.strip() for n in clasif.split("/")]
    if len(niveles) != 3:
        raise ValueError(f"Clasificación sin 3 niveles: {descripcion!r}")

    especie = especie.strip()
    return {
        "sequence_id": id_.strip(),
        "classification_raw": clasif,
        "te_class": niveles[0],
        "te_order": niveles[1],
        "te_superfamily": niveles[2],
        "species_raw": especie,
        "species_key": clave(especie),
    }


def leer_fasta(ruta, especies=None):
    """Genera un dict por secuencia, una a la vez. Si 'especies' (un set de
    species_key) está dado, solo devuelve las de esas especies."""
    for rec in SeqIO.parse(ruta, "fasta"):
        campos = separar_encabezado(rec.description)
        if especies is not None and campos["species_key"] not in especies:
            continue
        campos["sequence"] = normalizar_secuencia(str(rec.seq))
        yield campos