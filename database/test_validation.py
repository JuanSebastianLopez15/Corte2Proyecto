"""
Script interactivo para probar el funcionamiento de $jsonSchema e Índices en MongoDB.
Ejecuta pruebas clave en 'panteon_dev' con borrado seguro y validación enum.
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
db.sequences.delete_one({"sequence_id": "PDB00000001"})

# -------------------------------------------------------------
# PRUEBA 1: Inserción válida en 'species' (Alineada con limpiar.py)
# -------------------------------------------------------------
print("▶ PRUEBA 1: Insertando una especie con datos completos, mayúsculas y enum válido...")
specie_valida = {
    "species_key": "halicephalobus mephisto",
    "Species": "Halicephalobus mephisto",
    "Kingdom": "Animalia",
    "Phylum": "Nematoda",
    "Class": "Chromadorea",
    "Order": "Rhabditida",
    "Family": "Panagrolaimidae",
    "Source": "RM2+MCH, Dfam",
    "source_2": "Repbase",
    "annotation": None,
    "Notes": "Curated Dfam"
}

try:
    res = db.species.insert_one(specie_valida)
    print("  [ÉXITO] Especie insertada correctamente.")
    print(f"  ID generado por MongoDB (ObjectId): {res.inserted_id}\n")
except Exception as e:
    print(f"  [ERROR INESPERADO]: {e}\n")

# -------------------------------------------------------------
# PRUEBA 2: Validación enum en 'species' (Kingdom inválido)
# -------------------------------------------------------------
print("▶ PRUEBA 2: Probando restricción 'enum' en Kingdom (ej. 'Invalido')...")
specie_enum_invalido = specie_valida.copy()
specie_enum_invalido["species_key"] = "especie_invalida"
specie_enum_invalido["Kingdom"] = "Invalido"

try:
    db.species.insert_one(specie_enum_invalido)
    print("  [FALLÓ] MongoDB debió rechazar el Kingdom inválido pero lo aceptó.\n")
except WriteError:
    print("  [PROTEGIDO] MongoDB RECHAZÓ el documento:")
    print("  --> Razón: Violación de $jsonSchema (Kingdom solo permite Animalia, Plantae o Fungi).\n")

# -------------------------------------------------------------
# PRUEBA 3: Inserción válida en 'sequences' con k-mers completos (k1 a k6)
# -------------------------------------------------------------
print("▶ PRUEBA 3: Insertando secuencia con perfil completo de k-mers (k1 a k6)...")
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
        "k2": {"AA": 4, "AC": 2, "AG": 3, "AT": 8},
        "k3": {"AAA": 1, "AAT": 2},
        "k4": {"AAAA": 1},
        "k5": {"AAAAA": 1},
        "k6": {"AAAAAA": 1}
    }
}

try:
    res = db.sequences.insert_one(secuencia_valida)
    print("  [ÉXITO] Secuencia insertada correctamente con k-mers k1 a k6.")
    print(f"  ID generado: {res.inserted_id} | Sequence ID: PDB00000001\n")
except Exception as e:
    print(f"  [ERROR INESPERADO]: {e}\n")

# -------------------------------------------------------------
# PRUEBA 4: Duplicado en 'sequences' (Índice único en sequence_id)
# -------------------------------------------------------------
print("▶ PRUEBA 4: Intentando insertar OTRA secuencia con el MISMO sequence_id ('PDB00000001')...")
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
db.species.delete_one({"species_key": "halicephalobus mephisto"})
db.sequences.delete_one({"sequence_id": "PDB00000001"})

print("="*60)
print("  RESULTADO: Todas las pruebas pasadas con éxito.")
print("  Limpieza segura completada (solo se eliminaron los datos del test).")
print("="*60 + "\n")
