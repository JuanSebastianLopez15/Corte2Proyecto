"""Pipeline completo: lee el CSV y el FASTA de PanTEon y los carga en MongoDB.

Uso (desde la raíz del proyecto):
    python -m pipeline.cargar_todo --drop   # primera vez: crea todo desde cero
    python -m pipeline.cargar_todo          # si se cortó: carga solo lo que falta
"""
import argparse
import sys
import time
from pathlib import Path

import pandas as pd

import pipeline.carga as pc
from database.setup_db import setup_database
from pipeline.limpiar import limpiar_csv


def main(argv=None):
    p = argparse.ArgumentParser(description="Carga PanTEon (FASTA + CSV) en MongoDB.")
    p.add_argument("--uri", default="mongodb://localhost:27017", help="URI de MongoDB")
    p.add_argument("--db", default="panteon", help="nombre de la base de datos")
    p.add_argument("--fasta", default="data/PanTEon_Database_v1.6.1.fasta")
    p.add_argument("--csv", default="data/PanTEon_Database_metadata_v1.6.1.csv")
    p.add_argument("--tam", type=int, default=1000, help="documentos por lote")
    p.add_argument("--drop", action="store_true",
                   help="borra y recrea las colecciones antes de cargar")
    a = p.parse_args(argv)

    for ruta in (a.fasta, a.csv):
        if not Path(ruta).exists():
            sys.exit(f"No encuentro {ruta}. Descarga los datos de Zenodo (ver README).")

    t0 = time.perf_counter()
    db = setup_database(uri=a.uri, db_name=a.db, drop_existing=a.drop)

    # 1. species primero: MongoDB no comprueba referencias entre colecciones
    tabla = limpiar_csv(a.csv)
    existentes = set(db.species.distinct("species_key"))
    n_sp, rech_sp = pc.cargar_species(db, tabla[~tabla["species_key"].isin(existentes)])
    print(f"species:   {n_sp:,} insertadas | {len(rech_sp)} rechazadas")

    # 2. sequences por lotes (salta las que ya estén cargadas)
    n_sq, rech_sq = pc.cargar_lotes(db.sequences, pc.secuencias_pendientes(db, a.fasta),
                                    "sequence_id", tam=a.tam)
    print(f"sequences: {n_sq:,} insertadas | {len(rech_sq)} rechazadas")

    # 3. comprobaciones finales
    huerfanas = (set(db.sequences.distinct("species_key"))
                 - set(db.species.distinct("species_key")))
    print(f"Totales: species {db.species.count_documents({}):,} | "
          f"sequences {db.sequences.count_documents({}):,} | "
          f"huérfanas {len(huerfanas)} | {(time.perf_counter() - t0) / 60:.1f} min")

    if rech_sp or rech_sq:
        Path("reports").mkdir(exist_ok=True)
        pd.DataFrame(rech_sp + rech_sq, columns=["id", "codigo"]).to_csv(
            "reports/rechazos.csv", index=False)
        print("Hubo rechazos: ver reports/rechazos.csv")
    return 1 if (rech_sp or rech_sq or huerfanas) else 0


if __name__ == "__main__":
    sys.exit(main())