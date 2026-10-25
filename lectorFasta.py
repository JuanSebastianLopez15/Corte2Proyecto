# Lee el FASTA y extrae encabezado y estadísticas , tpdavia no guardamos secuencias
import re
import pandas as pd
from Bio import SeqIO

from config import norm

# Encabezado esperado: >PDB00000001#CLASSII/HELITRON/HELITRON @Halicephalobus mephisto
PATRON = re.compile(r"^(.+?)#(.+?)\s*@\s*(.+)$")   # id # clasificación @ especie


def leer_fasta(ruta):
    """Devuelve (DataFrame con una fila por secuencia, lista de encabezados inválidos)."""
    filas, malos = [], []
    for rec in SeqIO.parse(ruta, "fasta"):         # lee registro por registro (poca memoria)
        m = PATRON.match(rec.description)          # description = encabezado completo
        if not m:                                  # formato inesperado: se anota y se salta
            malos.append(rec.description)
            continue
        id_, clasif, especie = m.groups()
        niv = [n.strip() for n in clasif.split("/")]   # Clase / Orden / Superfamilia
        n_niveles = len(niv)                           # niveles que traía realmente
        niv += [None] * (3 - len(niv))                 # rellena con None si faltan
        seq = str(rec.seq).upper()
        filas.append({
            "seq_id": id_.strip(),
            "te_clase": niv[0], "te_orden": niv[1], "te_superfamilia": niv[2],  # del TE
            "n_niveles": n_niveles,
            "especie": re.sub(r"\s+", " ", especie.strip()),
            "longitud": len(seq),
            "n_N": seq.count("N"),                                      # cantidad de N
            "n_otros": len(seq) - sum(seq.count(c) for c in "ACGTN"),   # caracteres raros
        })
    df = pd.DataFrame(filas)
    df["especie_key"] = df["especie"].map(norm)    # llave normalizada para el cruce
    return df, malos