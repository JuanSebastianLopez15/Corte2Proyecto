"""Inicialización de la base de datos en MongoDB: esquemas $jsonSchema e índices."""

from pymongo import MongoClient, ASCENDING

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
                "description": "Clave única normalizada para cruce con FASTA",
            },
            "Species": {
                "bsonType": "string",
                "description": "Nombre científico original de la especie",
            },
            "Kingdom": {
                "bsonType": "string",
                "enum": ["Animalia", "Plantae", "Fungi"],
                "description": "Reino biológico (Animalia, Plantae o Fungi)",
            },
            "Phylum": {
                "bsonType": ["string", "null"],
                "description": "Phylum taxonómico",
            },
            "Class": {
                "bsonType": ["string", "null"],
                "description": "Clase taxonómica de la especie",
            },
            "Order": {
                "bsonType": ["string", "null"],
                "description": "Orden taxonómico de la especie",
            },
            "Family": {
                "bsonType": ["string", "null"],
                "description": "Familia taxonómica de la especie",
            },
            "Source": {
                "bsonType": ["string", "null"],
                "description": "Origen principal de la biblioteca de TEs (Dfam, RM2+MCH)",
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
                "description": "Procedencia y detalles del dataset",
            },
        },
    }
}

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
                "minLength": 1,
                "description": "Identificador original del FASTA (208.346 con prefijo PDB y 31.600 con nombres de la fuente)",
            },
            "species_key": {
                "bsonType": "string",
                "description": "Clave de cruce normalizada hacia species",
            },
            "species_raw": {
                "bsonType": "string",
                "description": "Texto original del encabezado después de @",
            },
            "te_class": {
                "bsonType": "string",
                "description": "Clase del elemento transponible",
            },
            "te_order": {
                "bsonType": "string",
                "description": "Orden del elemento transponible",
            },
            "te_superfamily": {
                "bsonType": ["string", "null"],
                "description": "Superfamilia del elemento transponible",
            },
            "classification_raw": {
                "bsonType": "string",
                "description": "Cadena completa de clasificación del encabezado FASTA",
            },
            "sequence": {
                "bsonType": "string",
                "description": "Secuencia completa de nucleótidos (A, C, G, T, N)",
            },
            "metrics": {
                "bsonType": "object",
                "required": ["length", "gc_content"],
                "properties": {
                    "length": {
                        "bsonType": ["int", "long"],
                        "minimum": 1,
                    },
                    "gc_content": {
                        "bsonType": ["double", "int"],
                        "minimum": 0.0,
                        "maximum": 100.0,
                        "description": "Porcentaje de GC sobre las bases conocidas: (G+C)/(A+C+G+T) * 100; las N no cuentan",
                    },
                    "n_count": {
                        "bsonType": ["int", "long"],
                        "minimum": 0,
                    },
                    "n_pct": {
                        "bsonType": ["double", "int"],
                        "minimum": 0.0,
                        "maximum": 100.0,
                        "description": "Porcentaje de N sobre la longitud total",
                    },
                },
            },
            "kmers": {
                "bsonType": "object",
                "required": ["k1", "k2", "k3", "k4", "k5", "k6"],
                "description": "Perfiles de k-mers (k1 a k6)",
            },
        },
    }
}


def setup_database(uri="mongodb://localhost:27017", db_name="panteon_dev", drop_existing=False):
    client = MongoClient(uri)
    db = client[db_name]

    colecciones = {
        "species": SCHEMA_SPECIES,
        "sequences": SCHEMA_SEQUENCES,
    }

    for nombre, esquema in colecciones.items():
        if drop_existing and nombre in db.list_collection_names():
            db[nombre].drop()

        if nombre not in db.list_collection_names():
            db.create_collection(
                nombre,
                validator=esquema,
                validationLevel="strict",
                validationAction="error",
            )
        else:
            db.command({
                "collMod": nombre,
                "validator": esquema,
                "validationLevel": "strict",
                "validationAction": "error",
            })

    # Índices en species
    db.species.create_index([("species_key", ASCENDING)], unique=True, name="idx_species_key_unique")
    db.species.create_index([("Kingdom", ASCENDING), ("Class", ASCENDING)], name="idx_kingdom_class")
    db.species.create_index([("Source", ASCENDING)], name="idx_species_source")

    # Índices en sequences
    db.sequences.create_index([("sequence_id", ASCENDING)], unique=True, name="idx_sequence_id_unique")
    db.sequences.create_index(
        [("species_key", ASCENDING), ("te_superfamily", ASCENDING)],
        name="idx_species_superfamily",
    )
    db.sequences.create_index(
        [("te_class", ASCENDING), ("te_order", ASCENDING), ("te_superfamily", ASCENDING)],
        name="idx_te_hierarchy",
    )
    db.sequences.create_index([("metrics.length", ASCENDING)], name="idx_metrics_length")
    db.sequences.create_index([("metrics.gc_content", ASCENDING)], name="idx_metrics_gc")

    print(f"Base '{db_name}' lista. Colecciones:", db.list_collection_names())
    return db


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Configura colecciones, $jsonSchema e índices en MongoDB.")
    parser.add_argument("--db", default="panteon_dev", help="Nombre de la base de datos")
    parser.add_argument("--drop", action="store_true", help="Borrar colecciones antes de crear")
    parser.add_argument("--uri", default="mongodb://localhost:27017", help="URI de MongoDB")

    args = parser.parse_args()
    setup_database(uri=args.uri, db_name=args.db, drop_existing=args.drop)
