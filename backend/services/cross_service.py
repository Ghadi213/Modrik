"""
File: services/cross_service.py
Purpose: Mendelian (Cross) analysis for father + mother results (JSON)

IMPORTANT:
- This module estimates inheritance risk using Mendelian genetics
  combined with ClinVar and PanelApp annotations.
- Results represent probabilistic risk estimation only.
- This is NOT a medical diagnosis.
"""

from typing import Dict, List, Any


# =========================================================
# 1) Text helpers
# =========================================================

def _norm_text(x: Any) -> str:
    """Convert None safely to empty string and strip spaces."""
    if x is None:
        return ""
    return str(x).strip()


def _is_pathogenic(sig: str) -> bool:
    """
    Accept:
    - Pathogenic
    - Likely pathogenic
    """
    return "pathogenic" in sig.lower()


# =========================================================
# 2) Disease name cleanup
# =========================================================

def _pick_best_disease_name(disease_names: str) -> str:
    """
    ClinVar may return multiple disease names separated by '|'.
    We choose the first useful one.
    """
    raw = _norm_text(disease_names)

    if not raw:
        return ""

    parts = [p.strip() for p in raw.split("|") if p.strip()]

    for p in parts:
        low = p.lower()
        if low not in ["not provided", "not specified"]:
            return p

    return parts[0] if parts else ""


# =========================================================
# 3) PanelApp helpers
# =========================================================

def _get_inheritance(panelapp: Dict, gene: str) -> str:
    """Get inheritance mode from PanelApp."""
    g = panelapp.get(gene, {})
    return _norm_text(g.get("mode_of_inheritance"))


def _is_x_linked(inheritance: str) -> bool:
    return "x-linked" in inheritance.lower()


def _is_monoallelic(inheritance: str) -> bool:
    return "monoallelic" in inheritance.lower()


def _is_biallelic(inheritance: str) -> bool:
    return "biallelic" in inheritance.lower()


def _has_both(inheritance: str) -> bool:
    return "both monoallelic and biallelic" in inheritance.lower()


def _friendly_inheritance_name(inheritance: str) -> str:
    """
    Convert PanelApp wording into cleaner label for UI.
    """
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


# =========================================================
# 4) Keep only pathogenic variants
# =========================================================

def _filter_variants(results: List[Dict]) -> List[Dict]:
    """
    Keep only pathogenic / likely pathogenic variants.
    """
    out = []

    for v in results:
        sig = _norm_text(v.get("clinvar__sig"))

        if not sig:
            continue

        if _is_pathogenic(sig):
            out.append(v)

    return out


# =========================================================
# 5) Group variants by gene
# =========================================================

def _index_by_gene(variants: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group all variants under each gene.
    """
    gene_map: Dict[str, List[Dict]] = {}

    for v in variants:
        gene = _norm_text(v.get("base__hugo"))

        if not gene:
            continue

        gene_map.setdefault(gene, []).append(v)

    return gene_map


# =========================================================
# 6) Zygosity helpers
# =========================================================

def _get_zygosity(variant_list: List[Dict]) -> str:
    """
    Extract zygosity directly from OpenCRAVAT result.

    Returns:
    - none
    - het
    - hom
    """
    if not variant_list:
        return "none"

    for v in variant_list:
        z = _norm_text(v.get("vcfinfo__zygosity")).lower()

        if z == "hom":
            return "hom"

        if z == "het":
            return "het"

    return "none"

# =========================================================
# NEW: Variant details (ADDED ONLY)
# =========================================================

def _variant_details(variant_list: List[Dict]) -> List[Dict]:
    """
    Return important variant-level details for expert review.
    """
    details = []

    for v in variant_list:
        details.append({
            "chrom": _norm_text(v.get("base__chrom")),
            "position": v.get("base__pos"),
            "ref": _norm_text(v.get("base__ref_base")),
            "alt": _norm_text(v.get("base__alt_base")),
            "gene": _norm_text(v.get("base__hugo")),
            "zygosity": _norm_text(v.get("vcfinfo__zygosity")),
            "clinical_significance": _norm_text(v.get("clinvar__sig")),
            "disease": _pick_best_disease_name(
                _norm_text(v.get("clinvar__disease_names"))
            ),
            "all_diseases": v.get("all_diseases", [])
        })

    return details

# =========================================================
# 7) Risk tables
# =========================================================

def _dominant_risk(father_state: str, mother_state: str):
    """
    Autosomal Dominant (Monoallelic)
    Based exactly on your table.

    Returns:
    affected, carrier, healthy
    """
    if father_state == "none" and mother_state == "none":
        return ("0%", "0%", "100%")

    if father_state == "het" and mother_state == "none":
        return ("50%", "0%", "50%")

    if father_state == "none" and mother_state == "het":
        return ("50%", "0%", "50%")

    if father_state == "het" and mother_state == "het":
        return ("75%", "0%", "25%")

    if father_state == "hom" and mother_state == "none":
        return ("100%", "0%", "0%")

    if father_state == "none" and mother_state == "hom":
        return ("100%", "0%", "0%")

    if father_state == "hom" and mother_state == "het":
        return ("100%", "0%", "0%")

    if father_state == "het" and mother_state == "hom":
        return ("100%", "0%", "0%")

    if father_state == "hom" and mother_state == "hom":
        return ("100%", "0%", "0%")

    return ("0%", "0%", "100%")


def _recessive_risk(father_state: str, mother_state: str):
    """
    Autosomal Recessive (Biallelic)
    Based exactly on your table.

    Returns:
    affected, carrier, healthy
    """
    if father_state == "none" and mother_state == "none":
        return ("0%", "0%", "100%")

    if father_state == "het" and mother_state == "none":
        return ("0%", "50%", "50%")

    if father_state == "none" and mother_state == "het":
        return ("0%", "50%", "50%")

    if father_state == "het" and mother_state == "het":
        return ("25%", "50%", "25%")

    if father_state == "hom" and mother_state == "none":
        return ("0%", "100%", "0%")

    if father_state == "none" and mother_state == "hom":
        return ("0%", "100%", "0%")

    if father_state == "hom" and mother_state == "het":
        return ("50%", "50%", "0%")

    if father_state == "het" and mother_state == "hom":
        return ("50%", "50%", "0%")

    if father_state == "hom" and mother_state == "hom":
        return ("100%", "0%", "0%")

    return ("0%", "0%", "100%")


def _x_linked_recessive_risk(father_state: str, mother_state: str):
    """
    X-Linked Recessive
    Based exactly on your table.

    Returns:
    sons_affected, sons_healthy,
    daughters_affected, daughters_carrier, daughters_healthy
    """

    # father none + mother none
    if father_state == "none" and mother_state == "none":
        return ("0%", "100%", "0%", "0%", "100%")

    # father none + mother het
    if father_state == "none" and mother_state == "het":
        return ("50%", "50%", "0%", "50%", "50%")

    # father none + mother hom
    if father_state == "none" and mother_state == "hom":
        return ("100%", "0%", "0%", "100%", "0%")

    # father mut + mother none
    # in your table this means affected father on X
    if father_state == "hom" and mother_state == "none":
        return ("0%", "100%", "0%", "100%", "0%")

    return ("0%", "100%", "0%", "0%", "100%")


def _x_linked_dominant_risk(father_state: str, mother_state: str):
    """
    X-Linked Dominant
    Based exactly on your table.

    Returns:
    sons_affected, sons_healthy,
    daughters_affected, daughters_healthy
    """

    # father none + mother none
    if father_state == "none" and mother_state == "none":
        return ("0%", "100%", "0%", "100%")

    # father none + mother het
    if father_state == "none" and mother_state == "het":
        return ("50%", "50%", "50%", "50%")

    # father mut + mother none
    if father_state == "hom" and mother_state == "none":
        return ("0%", "100%", "100%", "0%")

    return ("0%", "100%", "0%", "100%")


# =========================================================
# 8) Explain risk helpers
# =========================================================

def _explain_dominant_risk(father_state: str, mother_state: str) -> str:
    return (
        f"This gene follows Autosomal Dominant inheritance. "
        f"Father state: {father_state}. Mother state: {mother_state}. "
        f"The child risk is calculated using the dominant inheritance table."
    )


def _explain_recessive_risk(father_state: str, mother_state: str) -> str:
    return (
        f"This gene follows Autosomal Recessive inheritance. "
        f"Father state: {father_state}. Mother state: {mother_state}. "
        f"The child risk is calculated using the recessive inheritance table."
    )


def _explain_x_linked_recessive_risk(father_state: str, mother_state: str) -> str:
    return (
        f"This gene follows X-Linked Recessive inheritance. "
        f"Father state: {father_state}. Mother state: {mother_state}. "
        f"Male and female children may have different risk percentages."
    )


def _explain_x_linked_dominant_risk(father_state: str, mother_state: str) -> str:
    return (
        f"This gene follows X-Linked Dominant inheritance. "
        f"Father state: {father_state}. Mother state: {mother_state}. "
        f"Male and female children may have different risk percentages."
    )


def _explain_both_risk() -> str:
    return (
        "This gene may follow both dominant and recessive inheritance patterns. "
        "Because the inheritance is not straightforward, this result should be "
        "interpreted carefully by a genetics specialist."
    )


# =========================================================
# 9) Main cross analysis
# =========================================================

def cross_mendelian_analysis(
    male_data: Dict,
    female_data: Dict
) -> Dict:

    male_results = male_data.get("results", [])
    female_results = female_data.get("results", [])

    male_panelapp = male_data.get("panelapp_responses", {})
    female_panelapp = female_data.get("panelapp_responses", {})

    male_vars = _filter_variants(male_results)
    female_vars = _filter_variants(female_results)

    male_by_gene = _index_by_gene(male_vars)
    female_by_gene = _index_by_gene(female_vars)

    autosomal_dominant = []
    autosomal_recessive = []
    x_linked_recessive = []
    x_linked_dominant = []
    both_uncertain = []

    all_genes = set(male_by_gene.keys()) | set(female_by_gene.keys())

    for gene in sorted(all_genes):

        mv_list = male_by_gene.get(gene, [])
        fv_list = female_by_gene.get(gene, [])

        inh = _get_inheritance(male_panelapp, gene)

        if not inh:
           inh = _get_inheritance(female_panelapp, gene)

        father_state = _get_zygosity(mv_list)
        mother_state = _get_zygosity(fv_list)
       
        father_variants = _variant_details(mv_list)
        mother_variants = _variant_details(fv_list)

        parents_payload = {
            "father": {
                "state": father_state,
                "variants": father_variants
            },
            "mother": {
                "state": mother_state,
                "variants": mother_variants
            }
        }

        

        chosen = (mv_list + fv_list)[0]

        disease = _pick_best_disease_name(
            _norm_text(chosen.get("clinvar__disease_names"))
        )

        sig = _norm_text(chosen.get("clinvar__sig"))
        friendly_inheritance = _friendly_inheritance_name(inh)

        # =====================================================
        # BOTH MONOALLELIC + BIALLELIC
        # =====================================================
        if inh and _has_both(inh):
            both_uncertain.append({
                "gene": gene,
                "disease": disease,
                "clinical_significance": sig,
                "inheritance_mode": inh,
                "inheritance_label": friendly_inheritance,
                "father_state": father_state,
                "mother_state": mother_state,
                 "parents": parents_payload,
                "risk_explanation": _explain_both_risk(),
                "notes": "This gene may follow both dominant and recessive inheritance.",
                "recommendation": "Expert genetic interpretation recommended."
            })
            continue

        # =====================================================
        # X-LINKED
        # =====================================================
        if inh and _is_x_linked(inh):

            # X-linked recessive
            if "recessive" in inh.lower():
                sons_affected, sons_healthy, daughters_affected, daughters_carrier, daughters_healthy = _x_linked_recessive_risk(
                    father_state,
                    mother_state
                )

                x_linked_recessive.append({
                    "gene": gene,
                    "disease": disease,
                    "clinical_significance": sig,
                    "inheritance_mode": inh,
                    "inheritance_label": "X-Linked Recessive",
                    "father_state": father_state,
                    "mother_state": mother_state,
                    "parents": parents_payload,
                    "sons_affected": sons_affected,
                    "sons_healthy": sons_healthy,
                    "daughters_affected": daughters_affected,
                    "daughters_carrier": daughters_carrier,
                    "daughters_healthy": daughters_healthy,
                    "risk_explanation": _explain_x_linked_recessive_risk(
                        father_state,
                        mother_state
                    )
                })
                continue

            # X-linked dominant
            if "dominant" in inh.lower():
                sons_affected, sons_healthy, daughters_affected, daughters_healthy = _x_linked_dominant_risk(
                    father_state,
                    mother_state
                )

                x_linked_dominant.append({
                    "gene": gene,
                    "disease": disease,
                    "clinical_significance": sig,
                    "inheritance_mode": inh,
                    "inheritance_label": "X-Linked Dominant",
                    "father_state": father_state,
                    "mother_state": mother_state,
                    "parents": parents_payload,
                    "sons_affected": sons_affected,
                    "sons_healthy": sons_healthy,
                    "daughters_affected": daughters_affected,
                    "daughters_healthy": daughters_healthy,
                    "risk_explanation": _explain_x_linked_dominant_risk(
                        father_state,
                        mother_state
                    )
                })
                continue

        # =====================================================
        # AUTOSOMAL DOMINANT
        # =====================================================
        if inh and _is_monoallelic(inh):
            affected, carrier, healthy = _dominant_risk(
                father_state,
                mother_state
            )

            autosomal_dominant.append({
                "gene": gene,
                "disease": disease,
                "clinical_significance": sig,
                "inheritance_mode": inh,
                "inheritance_label": friendly_inheritance,
                "father_state": father_state,
                "mother_state": mother_state,
                "parents": parents_payload,
                "risk_affected_child": affected,
                "risk_carrier_child": carrier,
                "risk_unaffected_child": healthy,
                "risk_explanation": _explain_dominant_risk(
                    father_state,
                    mother_state
                )
            })

        # =====================================================
        # AUTOSOMAL RECESSIVE
        # =====================================================
        if inh and _is_biallelic(inh):
            affected, carrier, healthy = _recessive_risk(
                father_state,
                mother_state
            )

            autosomal_recessive.append({
                "gene": gene,
                "disease": disease,
                "clinical_significance": sig,
                "inheritance_mode": inh,
                "inheritance_label": friendly_inheritance,
                "father_state": father_state,
                "mother_state": mother_state,
                "parents": parents_payload,
                "risk_affected_child": affected,
                "risk_carrier_child": carrier,
                "risk_unaffected_child": healthy,
                "risk_explanation": _explain_recessive_risk(
                    father_state,
                    mother_state
                )
            })

    summary = {
        "dominant_count": len(autosomal_dominant),
        "recessive_count": len(autosomal_recessive),
        "x_linked_recessive_count": len(x_linked_recessive),
        "x_linked_dominant_count": len(x_linked_dominant),
        "both_uncertain_count": len(both_uncertain)
    }

    report_notes = [
        "This cross analysis estimates inheritance risk using Mendelian genetics.",
        "Results are based on ClinVar and PanelApp annotations.",
        "This report is not a medical diagnosis."
    ]

    return {
        "autosomal_dominant": autosomal_dominant,
        "autosomal_recessive": autosomal_recessive,
        "x_linked_recessive": x_linked_recessive,
        "x_linked_dominant": x_linked_dominant,
        "both_uncertain": both_uncertain,
        "summary": summary,
        "report_notes": report_notes
    }
