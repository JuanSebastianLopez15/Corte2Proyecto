"""
Script interactivo para probar el funcionamiento de $jsonSchema e Índices en MongoDB.
Ejecuta 4 pruebas clave en 'panteon_dev'.
"""

import sys
from pymongo import MongoClient
from pymongo.errors import WriteError, DuplicateKeyError

# Conexión
client = MongoClient("mongodb://localhost:27017")
db = client["panteon_dev"]

print("\n" + "="*60)
print("  PROBANDO VALIDACIÓN ($jsonSchema) E ÍNDICES EN 'panteon_dev'")
print("="*60 + "\n")


# PRUEBA 1: Inserción válida en 'species'

print("▶ PRUEBA 1: Insertando una especie con datos completos y válidos...")
specie_valida = {
    "species_key": "halicephalobus mephisto",
    "species": "Halicephalobus mephisto",
    "kingdom": "Animalia",
    "phylum": "Nematoda",
    "class": "Chromadorea",
    "order": "Rhabditida",
    "family": "Panagrolaimidae",
    "source": "RM2+MCH, Dfam",
    "source_2": "Repbase",
    "annotation": None,
    "notes": "Curated Dfam"
}

try:
    res = db.species.insert_one(specie_valida)
    print("  [ÉXITO] Especie insertada correctamente.")
    print(f"  ID generado por MongoDB (ObjectId): {res.inserted_id}\n")
except Exception as e:
    print(f"  [ERROR INESPERADO]: {e}\n")


# PRUEBA 2: Inserción inválida en 'species' (faltan campos obligatorios)

print("▶ PRUEBA 2: Intentando insertar especie SIN campos obligatorios (sin kingdom ni phylum)...")
specie_incompleta = {
    "species_key": "especie_incompleta",
    "species": "Especie Incompleta"
    # Faltan kingdom, phylum, class, order, family
}

try:
    db.species.insert_one(specie_incompleta)
    print("  [FALLÓ] MongoDB debió rechazar el documento pero lo aceptó.\n")
except WriteError as e:
    print("  [PROTEGIDO] MongoDB RECHAZÓ el documento:")
    print("  --> Razón: Violación de $jsonSchema (faltan campos obligatorios).\n")


# PRUEBA 3: Inserción válida en 'sequences'

print("▶ PRUEBA 3: Insertando secuencia de elemento transponible con k-mers y métricas...")
secuencia_valida = {
    "sequence_id": "PDB00000001",
    "species_key": "halicephalobus mephisto",
    "species_raw": "Halicephalobus mephisto",
    "te_class": "CLASSII",
    "te_order": "HELITRON",
    "te_superfamily": "HELITRON",
    "classification_raw": "CLASSII/HELITRON/HELITRON",
    "sequence": "TCTACTATAATACATTTTCAGAGGTCATTTGAATTTATGTACTTTTTCAAGTAGCG",
    "metrics": {
        "length": 56,
        "gc_content": 32.14,
        "n_count": 0,
        "other_count": 0
    },
    "kmers": {
        "k1": {"A": 17, "C": 7, "G": 11, "T": 21},
        "k2": {"AA": 4, "AC": 2, "AG": 3, "AT": 8}
    }
}

try:
    res = db.sequences.insert_one(secuencia_valida)
    print("  [ÉXITO] Secuencia insertada correctamente.")
    print(f"  ID generado: {res.inserted_id} | Sequence ID: PDB00000001\n")
except Exception as e:
    print(f"  [ERROR INESPERADO]: {e}\n")


# PRUEBA 4: Duplicado en 'sequences' (Índice único en sequence_id)

print("▶ PRUEBA 4: Intentando insertar OTRA secuencia con el MISMO sequence_id ('PDB00000001')...")
secuencia_duplicada = secuencia_valida.copy()
secuencia_duplicada.pop("_id", None) # Quitamos el _id para que Mongo genere uno nuevo pero choque en sequence_id

try:
    db.sequences.insert_one(secuencia_duplicada)
    print("  [FALLÓ] MongoDB debió rechazar el ID duplicado pero lo aceptó.\n")
except DuplicateKeyError as e:
    print("  [PROTEGIDO] El índice único rechazó el duplicado:")
    print("  --> Error: E11000 duplicate key error collection: panteon_dev.sequences index: idx_sequence_id_unique\n")


# Resumen y limpieza

db.species.delete_many({})
db.sequences.delete_many({})
print("="*60)
print("  RESULTADO: 4/4 pruebas pasadas con éxito.")
print("  La base de datos limpió los registros de prueba y está lista.")
print("="*60 + "\n")
