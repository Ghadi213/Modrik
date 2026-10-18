"""
Module: db_service.py
Purpose: Read OpenCRAVAT SQLite output and clean the data.

Expected:
- Return JSON-safe list of useful variant records
- Remove invalid disease names
- Drop records with no valid disease
"""

import os
import sqlite3
import pandas as pd
from utils.cleaners import safe_convert
from database import get_db_connection

def clean_disease_names(disease_names):
    """
    Clean disease names:
    - Remove not provided / not specified / unknown
    - Remove duplicates
    """
    if not disease_names:
        return []

    ignore_values = {
        "not provided",
        "not specified",
        "none",
        "unknown",
        "na",
        "n/a",
        ""
    }

    diseases = disease_names.split("|")
    cleaned = []

    for disease in diseases:
        disease = disease.strip()

        if disease.lower() in ignore_values:
            continue

        if disease and disease not in cleaned:
            cleaned.append(disease)

    return cleaned



def pick_best_disease_name(disease_names):
    """
    Return the first useful disease name after cleaning
    If no valid disease → return None
    """
    cleaned = clean_disease_names(disease_names)

    if cleaned:
        return cleaned[0]

    return None


def read_and_clean_sqlite(job_output_dir: str, job_name: str):

    db_file = os.path.join(job_output_dir, f"{job_name}.sqlite")

    conn = sqlite3.connect(db_file)

    query = """
    SELECT
        base__chrom,
        base__pos,
        base__ref_base,
        base__alt_base,
        base__hugo,
        clinvar__disease_names,
        clinvar__sig,
        vcfinfo__zygosity
    FROM variant
    WHERE
        base__chrom IS NOT NULL AND base__chrom != '' AND
        base__pos IS NOT NULL AND
        clinvar__disease_names IS NOT NULL AND TRIM(clinvar__disease_names) != '' AND
        base__ref_base IS NOT NULL AND base__ref_base != '' AND
        base__alt_base IS NOT NULL AND base__alt_base != '' AND
        base__hugo IS NOT NULL AND base__hugo != '' AND
        clinvar__sig IS NOT NULL AND clinvar__sig != '' AND
        vcfinfo__zygosity IS NOT NULL AND vcfinfo__zygosity != ''
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    df["all_diseases"] = df["clinvar__disease_names"].apply(clean_disease_names)
    df["best_disease_name"] = df["clinvar__disease_names"].apply(pick_best_disease_name)


    before_count = len(df)

    df = df[df["all_diseases"].apply(lambda x: len(x) > 0)]

    after_count = len(df)

    print(f"[INFO] Rows before cleaning: {before_count}")
    print(f"[INFO] Rows after cleaning: {after_count}")
    print(f"[INFO] Dropped rows: {before_count - after_count}")


    records = df.to_dict(orient="records")

    cleaned = [
        {k: safe_convert(v) for k, v in r.items()}
        for r in records
    ]

    return cleaned

