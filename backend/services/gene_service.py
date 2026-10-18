"""
Module: gene_service.py
Purpose: Extract gene symbols from cleaned OpenCRAVAT results.
Expected: Return unique list of gene names.
"""

def extract_genes(cleaned_results):
    genes = []

    for r in cleaned_results:
        if r.get("base__hugo"):
            genes.append(r["base__hugo"])

        if r.get("extra_vcf_info__GENE"):
            genes.append(r["extra_vcf_info__GENE"])

    genes = list(set([g for g in genes if g]))

    return genes