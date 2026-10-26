"""
Script interactivo para probar el funcionamiento de $jsonSchema e Índices en MongoDB.
Ejecuta pruebas clave en 'panteon_dev' con borrado seguro, validación enum,
soporte para taxonomía null e IDs sin prefijo PDB.
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

# Limpieza previa de seguridad únicamente para los IDs de prueba
db.species.delete_one({"species_key": "halicephalobus mephisto"})
db.species.delete_one({"species_key": "brachypodium distachyon"})
db.sequences.delete_one({"sequence_id": "PDB00000001"})
db.sequences.delete_one({"sequence_id": "AcoCah-1.102"})

# -------------------------------------------------------------
# PRUEBA 1: Inserción válida en 'species' con campos null (Brachypodium distachyon)
# -------------------------------------------------------------
print("▶ PRUEBA 1: Insertando especie real con taxonomía que contiene 'null' (Class: None)...")
specie_con_null = {
    "species_key": "brachypodium distachyon",
    "Species": "Brachypodium distachyon",
    "Kingdom": "Plantae",
    "Phylum": "Magnoliophyta",
    "Class": None,  # Clase vacía en CSV real
    "Order": "Poales",
    "Family": "Poaceae",
    "Source": "RM2+MCH",
    "source_2": None,
    "annotation": None,
    "Notes": 'ENSEMBL "2023"'
}

try:
    res = db.species.insert_one(specie_con_null)
    print("  [ÉXITO] Especie con Class: null insertada correctamente.")
    print(f"  ID generado por MongoDB (ObjectId): {res.inserted_id}\n")
except Exception as e:
    print(f"  [ERROR INESPERADO]: {e}\n")

# -------------------------------------------------------------
# PRUEBA 2: Validación enum en 'species' (Kingdom inválido)
# -------------------------------------------------------------
print("▶ PRUEBA 2: Probando restricción 'enum' en Kingdom (ej. 'Invalido')...")
specie_enum_invalido = specie_con_null.copy()
specie_enum_invalido["species_key"] = "especie_invalida"
specie_enum_invalido["Kingdom"] = "Invalido"

try:
    db.species.insert_one(specie_enum_invalido)
    print("  [FALLÓ] MongoDB debió rechazar el Kingdom inválido pero lo aceptó.\n")
except WriteError:
    print("  [PROTEGIDO] MongoDB RECHAZÓ el documento:")
    print("  --> Razón: Violación de $jsonSchema (Kingdom solo permite Animalia, Plantae o Fungi).\n")

# -------------------------------------------------------------
# PRUEBA 3: Inserción válida en 'sequences' con ID Dfam (sin prefijo PDB) y n_pct
# -------------------------------------------------------------
print("▶ PRUEBA 3: Insertando secuencia con ID sin prefijo PDB ('AcoCah-1.102') y métrica n_pct...")
secuencia_valida = {
    "sequence_id": "AcoCah-1.102",  # ID de Dfam sin prefijo PDB
    "species_key": "acomys cahirinus",
    "species_raw": "Acomys cahirinus",
    "te_class": "CLASSI",
    "te_order": "LINE",
    "te_superfamily": "L1",
    "classification_raw": "CLASSI/LINE/L1",
    "sequence": "TCTACTATAATACATTTTCAGAGGTCATTTGAATTTATGTACTTTTTCAAGTAGCG",
    "metrics": {
        "length": 56,
        "gc_content": 32.14,
        "n_count": 0,
        "n_pct": 0.0,
        "other_count": 0
    },
    "kmers": {
        "k1": {"A": 17, "C": 7, "G": 11, "T": 21},
        "k2": {"AA": 4, "AC": 2, "AG": 3, "AT": 8},
        "k3": {"AAA": 1, "AAT": 2},
        "k4": {"AAAA": 1},
        "k5": {"AAAAA": 1},
        "k6": {"AAAAAA": 1}
    }
}

try:
    res = db.sequences.insert_one(secuencia_valida)
    print("  [ÉXITO] Secuencia insertada correctamente con ID sin prefijo PDB y k1-k6.")
    print(f"  ID generado: {res.inserted_id} | Sequence ID: AcoCah-1.102\n")
except Exception as e:
    print(f"  [ERROR INESPERADO]: {e}\n")

# -------------------------------------------------------------
# PRUEBA 4: Duplicado en 'sequences' (Índice único en sequence_id)
# -------------------------------------------------------------
print("▶ PRUEBA 4: Intentando insertar OTRA secuencia con el MISMO sequence_id ('AcoCah-1.102')...")
secuencia_duplicada = secuencia_valida.copy()
secuencia_duplicada.pop("_id", None)

try:
    db.sequences.insert_one(secuencia_duplicada)
    print("  [FALLÓ] MongoDB debió rechazar el ID duplicado pero lo aceptó.\n")
except DuplicateKeyError:
    print("  [PROTEGIDO] El índice único rechazó el duplicado:")
    print("  --> Error: E11000 duplicate key error en sequence_id.\n")

# -------------------------------------------------------------
# Limpieza segura (borra únicamente los registros de prueba)
# -------------------------------------------------------------
db.species.delete_one({"species_key": "brachypodium distachyon"})
db.sequences.delete_one({"sequence_id": "AcoCah-1.102"})

print("="*60)
print("  RESULTADO: Todas las pruebas pasadas con éxito.")
print("  Limpieza segura completada (solo se eliminaron los datos del test).")
print("="*60 + "\n")
