"""
Module: panelapp_service.py
Purpose: Query PanelApp API using gene names.
"""

import requests
import time
from typing import List, Dict

PANELAPP_GENE_URL = "https://panelapp.genomicsengland.co.uk/api/v1/genes"
REQUEST_TIMEOUT = 10
RATE_LIMIT_DELAY = 0.5

def friendly_inheritance_name(inheritance: str) -> str:

    inh = inheritance.lower()

    if "both monoallelic and biallelic" in inh:
        return "Both Dominant and Recessive"

    if "x-linked" in inh and "dominant" in inh:
        return "X-Linked Dominant"

    if "x-linked" in inh and "recessive" in inh:
        return "X-Linked Recessive"

    if "x-linked" in inh:
        return "X-Linked"

    if "monoallelic" in inh:
        return "Autosomal Dominant"

    if "biallelic" in inh:
        return "Autosomal Recessive"

    return inheritance if inheritance else "Unknown"

def query_panelapp_gene(gene_name: str) -> Dict:
    url = f"{PANELAPP_GENE_URL}/{gene_name}/?format=json"
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def send_genes_to_panelapp(genes: List[str]) -> Dict[str, Dict]:
    """
    genes: list of gene names
    return: dict {gene_name: panelapp_data}
    """

    results = {}

    for gene in genes:
        try:
            data = query_panelapp_gene(gene)

            if data.get("results"):
                r = data["results"][0]
                results[gene] = {
                    "confidence_level": r.get("confidence_level"),
                    "mode_of_inheritance": r.get("mode_of_inheritance"),
                    "inheritance_label": friendly_inheritance_name( r.get("mode_of_inheritance", "")),
                    "mode_of_pathogenicity": r.get("mode_of_pathogenicity"),
                    "aliases": r.get("gene_data", {}).get("alias", [])
                }
            else:
                results[gene] = {"status": "not_found"}

        except Exception as e:
            results[gene] = {"error": str(e)}

        time.sleep(RATE_LIMIT_DELAY)

    return results