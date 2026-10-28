"""Pruebas de validación ($jsonSchema) e índices en panteon_dev."""

from pymongo import MongoClient
from pymongo.errors import WriteError, DuplicateKeyError

client = MongoClient("mongodb://localhost:27017")
db = client["panteon_dev"]

# Limpieza previa de los IDs de prueba
db.species.delete_one({"species_key": "brachypodium distachyon"})
db.sequences.delete_one({"sequence_id": "AcoCah-1.102"})

# 1. Inserción válida en species con Class: null
specie_con_null = {
    "species_key": "brachypodium distachyon",
    "Species": "Brachypodium distachyon",
    "Kingdom": "Plantae",
    "Phylum": "Magnoliophyta",
    "Class": None,
    "Order": "Poales",
    "Family": "Poaceae",
    "Source": "RM2+MCH",
    "source_2": None,
    "annotation": None,
    "Notes": 'ENSEMBL "2023"',
}

res = db.species.insert_one(specie_con_null)
print("Prueba 1 (species válida con null): OK | _id:", res.inserted_id)

# 2. Validación enum en Kingdom
specie_invalida = specie_con_null.copy()
specie_invalida["species_key"] = "especie_invalida"
specie_invalida["Kingdom"] = "Invalido"

try:
    db.species.insert_one(specie_invalida)
    print("Prueba 2 (enum Kingdom): FALLÓ")
except WriteError:
    print("Prueba 2 (rechazo por enum Kingdom): OK")

# 3. Inserción válida en sequences con ID sin PDB y n_pct
secuencia_valida = {
    "sequence_id": "AcoCah-1.102",
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
        "other_count": 0,
    },
    "kmers": {
        "k1": {"A": 17, "C": 7, "G": 11, "T": 21},
        "k2": {"AA": 4, "AC": 2, "AG": 3, "AT": 8},
        "k3": {"AAA": 1, "AAT": 2},
        "k4": {"AAAA": 1},
        "k5": {"AAAAA": 1},
        "k6": {"AAAAAA": 1},
    },
}

res = db.sequences.insert_one(secuencia_valida)
print("Prueba 3 (sequence válida con ID Dfam y k1-k6): OK | _id:", res.inserted_id)

# 4. Rechazo de duplicado por índice único en sequence_id
secuencia_duplicada = secuencia_valida.copy()
secuencia_duplicada.pop("_id", None)

try:
    db.sequences.insert_one(secuencia_duplicada)
    print("Prueba 4 (duplicado sequence_id): FALLÓ")
except DuplicateKeyError:
    print("Prueba 4 (rechazo duplicado por índice único): OK")

# Limpieza de los registros de prueba
db.species.delete_one({"species_key": "brachypodium distachyon"})
db.sequences.delete_one({"sequence_id": "AcoCah-1.102"})
print("Limpieza de registros de prueba completada.")
