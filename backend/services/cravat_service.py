"""
Module: cravat_service.py
Purpose: Run OpenCRAVAT on a given VCF file.
Expected: Generate SQLite output for downstream processing.
"""

import os
import subprocess

def run_opencravat(file_path: str, job_name: str, base_output_dir: str):
    job_output_dir = os.path.join(base_output_dir, f"oc_{job_name}")
    os.makedirs(job_output_dir, exist_ok=True)

    subprocess.run([
        "oc", "run",
        file_path,
        "-l", "hg38",
        "-d", job_output_dir,
        "-n", job_name,
        "-a", "clinvar"
    ], check=True)

    return job_output_dir