import os
import tempfile
from fastapi import UploadFile
from services.cravat_service import run_opencravat
from services.db_service import read_and_clean_sqlite
from services.gene_service import extract_genes
from services.panelapp_service import send_genes_to_panelapp
from services.cross_service import cross_mendelian_analysis

async def analyze_one_vcf(file: UploadFile) -> dict:
   temp_dir = tempfile.mkdtemp(prefix="genome_job_")
   file_path = os.path.join(temp_dir, file.filename)
   with open(file_path, "wb") as f:
       f.write(await file.read())
   job_name = os.path.splitext(file.filename)[0]
   
   # 1) Run OpenCRAVAT
   job_output_dir = run_opencravat(file_path, job_name, temp_dir)
   # 2) Read SQLite Results
   cleaned_results = read_and_clean_sqlite(
       job_output_dir,
       job_name
   )
   # 3) Variant Details
   for r in cleaned_results:
       r["variant_details"] = {
           "chrom": r.get("base__chrom"),
           "position": r.get("base__pos"),
           "ref": r.get("base__ref_base"),
           "alt": r.get("base__alt_base"),
           "zygosity": r.get("vcfinfo__zygosity"),
       }
   # 4) Extract Genes
   genes = extract_genes(cleaned_results)
   # 5) PanelApp
   panelapp_results = send_genes_to_panelapp(genes)
   return {
       "message": "Analysis complete",
       "job_name": job_name,
       "gene_count": len(genes),
       "genes_sent_to_panelapp": genes,
       "panelapp_responses": panelapp_results,
       "results": cleaned_results
   }

async def analyze_cross_vcf(
   male_file: UploadFile,
   female_file: UploadFile
) -> dict:
   male_result = await analyze_one_vcf(male_file)
   female_result = await analyze_one_vcf(female_file)
   cross_result = cross_mendelian_analysis(
       male_data=male_result,
       female_data=female_result
   )
   return {
       "message": "Cross analysis complete",
       "male_job": male_result.get("job_name"),
       "female_job": female_result.get("job_name"),
       "cross_results": cross_result
   }