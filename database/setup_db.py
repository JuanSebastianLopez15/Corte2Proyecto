"""
Módulo de inicialización de la Base de Datos para el proyecto PanTEon.
Configura las colecciones con validación estructural ($jsonSchema) e índices estratégicos.
"""

from pymongo import MongoClient, ASCENDING
from pymongo.errors import CollectionInvalid, OperationFailure


# 1. Esquema de validación para la colección 'species'
# Alineado con las columnas de pipeline/limpiar.py:
# - Mayúscula inicial para columnas originales del CSV
# - Minúsculas para columnas calculadas (species_key, source_2, annotation)
# - Restricciones 'enum' para Kingdom, source_2 y Notes

SCHEMA_SPECIES = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "species_key",
            "Species",
            "Kingdom",
            "Phylum",
            "Class",
            "Order",
            "Family",
        ],
        "properties": {
            "species_key": {
                "bsonType": "string",
                "description": "Clave única normalizada para cruce con FASTA (minúsculas, sin espacios extras)",
            },
            "Species": {
                "bsonType": "string",
                "description": "Nombre científico original de la especie",
            },
            "Kingdom": {
                "bsonType": "string",
                "enum": ["Animalia", "Plantae", "Fungi"],
                "description": "Reino biológico restringido a Animalia, Plantae o Fungi",
            },
            "Phylum": {
                "bsonType": "string",
                "description": "Phylum taxonómico",
            },
            "Class": {
                "bsonType": "string",
                "description": "Clase taxonómica de la especie (organismo)",
            },
            "Order": {
                "bsonType": "string",
                "description": "Orden taxonómico de la especie (organismo)",
            },
            "Family": {
                "bsonType": "string",
                "description": "Familia taxonómica de la especie",
            },
            "Source": {
                "bsonType": ["string", "null"],
                "description": "Origen principal de la biblioteca de TEs (ej. Dfam, RM2+MCH)",
            },
            "source_2": {
                "bsonType": ["string", "null"],
                "enum": ["Repbase", "Dfam", None],
                "description": "Origen secundario validado (Repbase, Dfam o null)",
            },
            "annotation": {
                "bsonType": ["string", "null"],
                "description": "Notas o anotaciones extra separadas de Source 2",
            },
            "Notes": {
                "bsonType": ["string", "null"],
                "enum": [
                    "B-GUT",
                    'ENSEMBL "2023"',
                    'ENSEMBL "2025"',
                    "Curated Dfam",
                    "Uncurated Dfam",
                    "Dfam no especie",
                    "Release 1.2",
                    "No especie Repbase",
                    "APTEdb",
                    None,
                ],
                "description": "Procedencia y detalles con valores discretos del dataset",
            },
        },
    }
}


# 2. Esquema de validación para la colección 'sequences'
# Exige k-mers completos de k1 a k6

SCHEMA_SEQUENCES = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "sequence_id",
            "species_key",
            "te_class",
            "te_order",
            "sequence",
            "metrics",
            "kmers",
        ],
        "properties": {
            "sequence_id": {
                "bsonType": "string",
                "pattern": "^PDB[0-9]+$",
                "description": "Identificador original de la secuencia (ej. PDB00000001)",
            },
            "species_key": {
                "bsonType": "string",
                "description": "Clave de cruce normalizada hacia la colección species",
            },
            "species_raw": {
                "bsonType": "string",
                "description": "Texto original del encabezado del FASTA después de @",
            },
            "te_class": {
                "bsonType": "string",
                "description": "Clase del elemento transponible (ej. CLASSI, CLASSII)",
            },
            "te_order": {
                "bsonType": "string",
                "description": "Orden del elemento transponible (ej. LTR, HELITRON, TIR)",
            },
            "te_superfamily": {
                "bsonType": ["string", "null"],
                "description": "Superfamilia del TE (ej. GYPSY, COPIA, HELITRON). Puede ser null si el TE no tiene nivel 3",
            },
            "classification_raw": {
                "bsonType": "string",
                "description": "Cadena completa de clasificación tal como viene en el encabezado FASTA",
            },
            "sequence": {
                "bsonType": "string",
                "description": "Secuencia completa de nucleótidos (mayúsculas: A, C, G, T, N)",
            },
            "metrics": {
                "bsonType": "object",
                "required": ["length", "gc_content"],
                "properties": {
                    "length": {
                        "bsonType": ["int", "long"],
                        "minimum": 1,
                        "description": "Longitud de la secuencia en nucleótidos",
                    },
                    "gc_content": {
                        "bsonType": ["double", "int"],
                        "minimum": 0.0,
                        "maximum": 100.0,
                        "description": "Porcentaje de contenido GC ((G+C)/longitud * 100)",
                    },
                    "n_count": {
                        "bsonType": ["int", "long"],
                        "minimum": 0,
                        "description": "Cantidad de bases no determinadas (N)",
                    },
                    "other_count": {
                        "bsonType": ["int", "long"],
                        "minimum": 0,
                        "description": "Cantidad de caracteres fuera del alfabeto estándar",
                    },
                },
            },
            "kmers": {
                "bsonType": "object",
                "required": ["k1", "k2", "k3", "k4", "k5", "k6"],
                "description": "Diccionario con los perfiles completos de k-mers (k1 a k6)",
            },
        },
    }
}


def setup_database(uri="mongodb://localhost:27017", db_name="panteon_dev", drop_existing=False):
    """
    Inicializa la base de datos con colecciones validadas e índices.
    
    Args:
        uri: Dirección de conexión a MongoDB.
        db_name: Nombre de la base de datos ('panteon_dev' o 'panteon').
        drop_existing: Si es True, borra las colecciones previas para reiniciar en limpio.
    """
    client = MongoClient(uri)
    db = client[db_name]

    print(f"=== Inicializando Base de Datos: '{db_name}' en {uri} ===")

    # 1. Preparar colecciones
    colecciones = {
        "species": SCHEMA_SPECIES,
        "sequences": SCHEMA_SEQUENCES,
    }

    for nombre, esquema in colecciones.items():
        if drop_existing and nombre in db.list_collection_names():
            print(f"[*] Eliminando colección existente '{nombre}'...")
            db[nombre].drop()

        if nombre not in db.list_collection_names():
            print(f"[*] Creando colección '{nombre}' con validación $jsonSchema...")
            db.create_collection(
                nombre,
                validator=esquema,
                validationLevel="strict",
                validationAction="error",
            )
        else:
            print(f"[*] Actualizando validador de colección existente '{nombre}'...")
            db.command({
                "collMod": nombre,
                "validator": esquema,
                "validationLevel": "strict",
                "validationAction": "error",
            })



    # 2. Creación de Índices Estratégicos


    print("\n=== Configurando Índices Estratégicos ===")

    # Índices en 'species' (Alineados con mayúsculas de limpiar.py)
    print("[*] Índices en colección 'species'...")
    # Índice único para garantizar clave de cruce sin duplicados
    db.species.create_index([("species_key", ASCENDING)], unique=True, name="idx_species_key_unique")
    # Índice para consultas y filtros por reino y clase taxonómica
    db.species.create_index([("Kingdom", ASCENDING), ("Class", ASCENDING)], name="idx_kingdom_class")
    # Índice para comparaciones por origen (Dfam vs RM2+MCH)
    db.species.create_index([("Source", ASCENDING)], name="idx_species_source")

    # Índices en 'sequences'
    print("[*] Índices en colección 'sequences'...")
    # Índice único por ID original del FASTA (búsqueda obligatoria consulta 8)
    db.sequences.create_index([("sequence_id", ASCENDING)], unique=True, name="idx_sequence_id_unique")
    # Índice compuesto para buscar superfamilias dentro de una especie (consulta 9 y exportador)
    db.sequences.create_index(
        [("species_key", ASCENDING), ("te_superfamily", ASCENDING)],
        name="idx_species_superfamily"
    )
    # Índice compuesto para agregaciones y conteos de jerarquía TE (consultas 1, 2, 3 y 5)
    db.sequences.create_index(
        [("te_class", ASCENDING), ("te_order", ASCENDING), ("te_superfamily", ASCENDING)],
        name="idx_te_hierarchy"
    )
    # Índice para consultas de longitud extrema y ordenamientos (consultas 5 y 7)
    db.sequences.create_index([("metrics.length", ASCENDING)], name="idx_metrics_length")
    # Índice para consultas de contenido GC (consulta 6)
    db.sequences.create_index([("metrics.gc_content", ASCENDING)], name="idx_metrics_gc")

    print("\n✓ Configuración completada con éxito.")
    
    # Resumen de índices creados
    print("\n--- Índices actuales en 'species' ---")
    for idx in db.species.list_indexes():
        print(f" - {idx['name']}: {idx['key']}")

    print("\n--- Índices actuales en 'sequences' ---")
    for idx in db.sequences.list_indexes():
        print(f" - {idx['name']}: {idx['key']}")

    return db


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Configuración de base de datos MongoDB con $jsonSchema e índices.")
    parser.add_argument("--db", default="panteon_dev", help="Nombre de la base de datos (panteon_dev o panteon)")
    parser.add_argument("--drop", action="store_true", help="Eliminar colecciones previas antes de crear")
    parser.add_argument("--uri", default="mongodb://localhost:27017", help="URI de conexión a MongoDB")

    args = parser.parse_args()
    setup_database(uri=args.uri, db_name=args.db, drop_existing=args.drop)
