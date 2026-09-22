"""
Generate Synthetic Clinical Trial Protocol PDFs
Creates realistic synthetic protocol PDFs for instant testing and drag-and-drop.
Uses a self-contained pure-Python PDF writer (zero dependencies).
"""

import os

def create_simple_pdf(filename: str, title: str, sections: list):
    """Writes a valid PDF 1.4 file with text pages."""
    text_content = f"{title}\n" + "=" * len(title) + "\n\n"
    for sec_title, sec_body in sections:
        text_content += f"{sec_title}\n" + "-" * len(sec_title) + "\n"
        text_content += sec_body.strip() + "\n\n"

    # Minimal clean PDF 1.4 generation
    lines = text_content.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").split("\n")
    stream_lines = ["BT", "/F1 10 Tf", "50 750 Td", "14 TL"]
    for line in lines:
        if line.startswith("="):
            stream_lines.append(f"({line[:40]}) Tj T*")
        elif line.startswith("-"):
            stream_lines.append(f"({line[:40]}) Tj T*")
        else:
            # Wrap lines if long
            while len(line) > 75:
                part = line[:75]
                line = line[75:]
                stream_lines.append(f"({part}) Tj T*")
            stream_lines.append(f"({line}) Tj T*")
    stream_lines.append("ET")
    stream_data = "\n".join(stream_lines).encode("latin1", errors="replace")

    objects = []
    # 1: Catalog
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    # 2: Pages
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    # 3: Page
    objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>")
    # 4: Stream
    stream_obj = f"<< /Length {len(stream_data)} >>\nstream\n".encode("ascii") + stream_data + b"\nendstream"
    objects.append(stream_obj)
    # 5: Font
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects):
        offsets.append(len(pdf))
        pdf.extend(f"{i+1} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii"))

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        f.write(pdf)
    print(f"Generated synthetic PDF: {filename} ({len(pdf)} bytes)")


if __name__ == "__main__":
    out_dir = "sample_data"
    
    # PDF 1
    create_simple_pdf(
        os.path.join(out_dir, "NCT05423189_EGFR_NSCLC_Protocol.pdf"),
        "CLINICAL STUDY PROTOCOL: NCT05423189",
        [
            ("Study Title", "A Phase 3, Multicenter Study of Novel TKI in Patients with Locally Advanced or Metastatic EGFRm Non-Small Cell Lung Cancer After Progression on Prior Osimertinib."),
            ("Phase and Indication", "Phase III. Primary Condition: Advanced/Metastatic Non-Small Cell Lung Cancer (NSCLC)."),
            ("Inclusion Criteria", 
             "1. Age >= 18 years at the time of screening.\n"
             "2. Histologically or cytologically confirmed metastatic Non-Small Cell Lung Cancer (Stage IV).\n"
             "3. Documented activating EGFR mutation (Exon 19 del or L858R).\n"
             "4. Documented radiographic disease progression following prior 3rd generation EGFR-TKI (Osimertinib).\n"
             "5. ECOG performance status 0 or 1.\n"
             "6. Adequate hematologic and organ function: ANC >= 1500/uL, Platelets >= 100,000/uL, Serum creatinine <= 1.5x ULN."),
            ("Exclusion Criteria",
             "1. Active, untreated or symptomatic central nervous system (CNS) brain metastases.\n"
             "2. History of drug-induced interstitial lung disease (ILD) or radiation pneumonitis requiring steroids.\n"
             "3. Significant cardiovascular disease including NYHA Class III/IV heart failure or QTc > 470 ms.")
        ]
    )

    # PDF 2
    create_simple_pdf(
        os.path.join(out_dir, "NCT04891120_PDL1_Immunotherapy_Protocol.pdf"),
        "CLINICAL STUDY PROTOCOL: NCT04891120",
        [
            ("Study Title", "Phase 2 Basket Trial of Dual Immune Checkpoint Inhibitor in Advanced Solid Tumors with High PD-L1 Expression."),
            ("Phase and Indication", "Phase II. Primary Condition: Advanced Solid Tumors with PD-L1 TPS >= 50%."),
            ("Inclusion Criteria",
             "1. Age >= 18 years.\n"
             "2. Documented PD-L1 TPS >= 50% by validated IHC assay.\n"
             "3. ECOG Performance Status 0 or 1.\n"
             "4. Adequate hepatic function: Bilirubin <= 1.5x ULN, AST/ALT <= 2.5x ULN."),
            ("Exclusion Criteria",
             "1. Active autoimmune disease requiring systemic corticosteroids > 10mg/day prednisone equivalent.\n"
             "2. Prior severe immune-related adverse events (irAE >= Grade 3).")
        ]
    )

    # PDF 3
    create_simple_pdf(
        os.path.join(out_dir, "NCT05219903_HER2_Targeted_ADC_Protocol.pdf"),
        "CLINICAL STUDY PROTOCOL: NCT05219903",
        [
            ("Study Title", "Phase 1/2 Study of Novel HER2-Targeted Antibody Drug Conjugate in HER2-Expressing Carcinomas."),
            ("Phase and Indication", "Phase I/II. Primary Condition: HER2-positive or HER2-mutant Carcinomas."),
            ("Inclusion Criteria",
             "1. Age >= 18 years.\n"
             "2. Histologically confirmed HER2-positive (IHC 3+ or ISH+) or HER2-mutant solid tumors.\n"
             "3. Baseline left ventricular ejection fraction (LVEF) >= 50% by echo or MUGA."),
            ("Exclusion Criteria",
             "1. History of symptomatic heart failure (NYHA II-IV) or LVEF < 50%.\n"
             "2. Active non-infectious pneumonitis or interstitial lung disease.")
        ]
    )
