"""
Report Generator Module
Produces comprehensive, downloadable researcher review reports in both Markdown
and styled HTML / printable PDF formats for clinical trial adjudication.
"""

from datetime import datetime
from typing import Dict, Any, List


def generate_markdown_report(
    patient_profile: Dict[str, Any],
    matching_results: List[Dict[str, Any]],
    patient_identifier: str = "SYNTHETIC-PT-8092"
) -> str:
    """
    Generates a rigorous, structured Markdown clinical review report.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    demo = patient_profile.get("demographics", {})
    cond = patient_profile.get("condition", {})
    biomarkers = patient_profile.get("biomarkers", [])
    prior_tx = patient_profile.get("prior_treatments", [])
    labs = patient_profile.get("organ_function_and_labs", {})

    md = []
    md.append("# Clinical Trial Eligibility Adjudication Report")
    md.append(f"**Generated:** {now_str} | **System:** GenAI Clinical Trial Eligibility Matcher")
    md.append(f"**Patient Synthetic ID:** `{patient_identifier}` *(Synthetic / De-identified Data Only)*\n")
    md.append("---\n")

    # Section 1: Patient Summary
    md.append("## 1. Structured Patient Clinical Profile\n")
    md.append(f"- **Demographics:** Age {demo.get('age', 'N/A')} | Sex: {demo.get('gender', 'N/A')} | ECOG Performance Status: {demo.get('ecog_ps', 'N/A')}")
    md.append(f"- **Primary Diagnosis:** {cond.get('primary_diagnosis', 'N/A')}")
    md.append(f"- **Histology & Stage:** {cond.get('histology', 'N/A')}, {cond.get('stage', 'N/A')} ({cond.get('progression_status', 'N/A')})")

    if biomarkers:
        bio_str = ", ".join([f"**{b.get('gene', '')}**: {b.get('status', '')} ({b.get('details', '')})" for b in biomarkers])
        md.append(f"- **Documented Biomarkers:** {bio_str}")

    if prior_tx:
        tx_str = "; ".join([f"{t.get('name', '')} (Line {t.get('line', 1)} - {t.get('outcome', '')})" for t in prior_tx])
        md.append(f"- **Prior Therapies:** {tx_str}")

    if labs:
        labs_str = " | ".join([f"{k.upper()}: {v}" for k, v in labs.items()])
        md.append(f"- **Screening Labs & Organ Function:** {labs_str}")

    md.append(f"- **CNS Metastases:** {patient_profile.get('cns_metastases', 'Unknown')}\n")
    md.append("---\n")

    # Section 2: Executive Summary Table
    md.append("## 2. Trial Matching Overview\n")
    md.append("| Trial ID | Phase | Primary Indication | Match Confidence | Overall Status | Missing Data Count |")
    md.append("| :--- | :--- | :--- | :---: | :---: | :---: |")

    for res in matching_results:
        trial = res.get("trial", {})
        eval_data = res.get("evaluation", {})
        tid = trial.get("trial_id", "N/A")
        phase = trial.get("phase", "N/A")
        indication = trial.get("condition", "N/A")
        conf = eval_data.get("match_confidence", 0)
        status = eval_data.get("overall_eligibility", "PENDING")
        missing_count = len(eval_data.get("missing_information", []))
        md.append(f"| **{tid}** | {phase} | {indication} | **{conf}%** | `{status}` | {missing_count} item(s) |")

    md.append("\n---\n")

    # Section 3: Deep Per-Trial Breakdown
    md.append("## 3. Protocol Criteria Adjudications\n")

    for idx, res in enumerate(matching_results, 1):
        trial = res.get("trial", {})
        eval_data = res.get("evaluation", {})
        tid = trial.get("trial_id", f"TRIAL-{idx}")
        title = trial.get("trial_title", "Clinical Protocol")
        status = eval_data.get("overall_eligibility", "UNKNOWN")
        conf = eval_data.get("match_confidence", 0)
        summary = eval_data.get("executive_summary", "")

        md.append(f"### 3.{idx} Trial: {tid} - {title}\n")
        md.append(f"- **Adjudicated Status:** `{status}`")
        md.append(f"- **Match Alignment Confidence:** **{conf}%**")
        md.append(f"- **Executive Rationale:** {summary}\n")

        # Inclusions
        inclusions = eval_data.get("evaluated_inclusions", [])
        if inclusions:
            md.append("#### Inclusion Criteria Evaluation:")
            md.append("| ID | Criterion Specification | Status | Patient Evidence & Rationale | Citation |")
            md.append("| :--- | :--- | :---: | :--- | :--- |")
            for inc in inclusions:
                status_icon = "MET" if inc.get("status") == "MET" else ("UNMET" if inc.get("status") == "UNMET" else "MISSING")
                md.append(
                    f"| `{inc.get('id')}` | {inc.get('criterion')} | **[{status_icon}]** | "
                    f"{inc.get('evidence')} *({inc.get('explanation')})* | *{inc.get('citation')}* |"
                )
            md.append("")

        # Exclusions
        exclusions = eval_data.get("evaluated_exclusions", [])
        if exclusions:
            md.append("#### Exclusion Criteria Evaluation:")
            md.append("| ID | Exclusion Rule | Status (Avoided) | Patient Evidence & Safety Check | Citation |")
            md.append("| :--- | :--- | :---: | :--- | :--- |")
            for exc in exclusions:
                status_icon = "MET" if exc.get("status") == "MET" else ("TRIGGERED" if exc.get("status") == "UNMET" else "MISSING")
                md.append(
                    f"| `{exc.get('id')}` | {exc.get('criterion')} | **[{status_icon}]** | "
                    f"{exc.get('evidence')} *({exc.get('explanation')})* | *{exc.get('citation')}* |"
                )
            md.append("")

        # Missing Information
        missing = eval_data.get("missing_information", [])
        if missing:
            md.append("#### Required Information Checklist (Researcher Action Required):")
            for m in missing:
                md.append(f"- [ ] **ACTION ITEM:** Verify `{m}` in electronic health records or order baseline screening.")
            md.append("")

        md.append("---\n")

    md.append("### Regulatory & Compliance Notice")
    md.append(
        "> *Notice: This automated adjudication report was generated using Artificial Intelligence (GenAI & RAG) "
        "for research decision-support only. Final subject enrollment eligibility requires verification by the "
        "Principal Investigator (PI) against institutional review board (IRB) approved protocol documents.*"
    )

    return "\n".join(md)


def generate_html_report(
    patient_profile: Dict[str, Any],
    matching_results: List[Dict[str, Any]],
    patient_identifier: str = "SYNTHETIC-PT-8092"
) -> str:
    """
    Generates a beautifully styled, high-contrast HTML report suitable for browser viewing or PDF printing.
    """
    now_str = datetime.now().strftime("%B %d, %Y - %H:%M UTC")
    demo = patient_profile.get("demographics", {})
    cond = patient_profile.get("condition", {})
    biomarkers = patient_profile.get("biomarkers", [])

    cards_html = ""
    for idx, res in enumerate(matching_results, 1):
        trial = res.get("trial", {})
        eval_data = res.get("evaluation", {})
        tid = trial.get("trial_id", f"TRIAL-{idx}")
        title = trial.get("trial_title", "Clinical Protocol")
        status = eval_data.get("overall_eligibility", "PENDING")
        conf = eval_data.get("match_confidence", 0)

        badge_class = "badge-eligible" if status == "ELIGIBLE" else ("badge-action" if "POTENTIAL" in status else "badge-ineligible")

        inclusions_rows = ""
        for inc in eval_data.get("evaluated_inclusions", []):
            st = inc.get("status", "MET")
            chip = "chip-met" if st == "MET" else ("chip-unmet" if st == "UNMET" else "chip-missing")
            inclusions_rows += f"""
            <tr>
              <td><strong>{inc.get('id')}</strong></td>
              <td>{inc.get('criterion')}</td>
              <td><span class="chip {chip}">{st}</span></td>
              <td>{inc.get('evidence')}</td>
              <td class="citation">{inc.get('citation')}</td>
            </tr>
            """

        exclusions_rows = ""
        for exc in eval_data.get("evaluated_exclusions", []):
            st = exc.get("status", "MET")
            chip = "chip-met" if st == "MET" else ("chip-unmet" if st == "UNMET" else "chip-missing")
            display_st = "AVOIDED" if st == "MET" else ("TRIGGERED" if st == "UNMET" else "MISSING")
            exclusions_rows += f"""
            <tr>
              <td><strong>{exc.get('id')}</strong></td>
              <td>{exc.get('criterion')}</td>
              <td><span class="chip {chip}">{display_st}</span></td>
              <td>{exc.get('evidence')}</td>
              <td class="citation">{exc.get('citation')}</td>
            </tr>
            """

        missing_items = "".join([f"<li>{m}</li>" for m in eval_data.get("missing_information", [])])

        cards_html += f"""
        <div class="trial-card">
          <div class="trial-header">
            <div>
              <span class="trial-id">{tid}</span>
              <h3 class="trial-title">{title}</h3>
              <p class="trial-sub">{trial.get('phase', '')} &bull; {trial.get('condition', '')}</p>
            </div>
            <div class="score-badge">
              <span class="status-badge {badge_class}">{status}</span>
              <div class="conf-text">{conf}% Alignment</div>
            </div>
          </div>
          <p class="summary-box"><strong>Executive Review:</strong> {eval_data.get('executive_summary', '')}</p>
          
          <h4 class="section-label">Inclusion Criteria Adjudication</h4>
          <table>
            <thead><tr><th>ID</th><th>Criterion</th><th>Status</th><th>Evidence</th><th>Citation</th></tr></thead>
            <tbody>{inclusions_rows}</tbody>
          </table>

          <h4 class="section-label">Exclusion Criteria Adjudication</h4>
          <table>
            <thead><tr><th>ID</th><th>Criterion</th><th>Status</th><th>Evidence</th><th>Citation</th></tr></thead>
            <tbody>{exclusions_rows}</tbody>
          </table>

          {f'''<div class="missing-box">
            <strong>Actionable Missing Clinical Information:</strong>
            <ul>{missing_items}</ul>
          </div>''' if missing_items else ''}
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Clinical Trial Eligibility Adjudication Report - {patient_identifier}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; padding: 40px; }}
  .container {{ max-width: 1000px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }}
  .header {{ border-bottom: 2px solid #008080; padding-bottom: 20px; margin-bottom: 30px; }}
  .header h1 {{ color: #0b192c; margin: 0 0 8px 0; font-size: 26px; }}
  .meta {{ color: #64748b; font-size: 14px; }}
  .patient-card {{ background: #f1f5f9; border-radius: 8px; padding: 20px; margin-bottom: 30px; border-left: 4px solid #008080; }}
  .patient-card h2 {{ font-size: 18px; margin-top: 0; color: #0b192c; }}
  .trial-card {{ border: 1px solid #cbd5e1; border-radius: 10px; padding: 24px; margin-bottom: 30px; page-break-inside: avoid; }}
  .trial-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }}
  .trial-id {{ font-size: 12px; font-weight: 700; background: #e0f2fe; color: #0369a1; padding: 3px 8px; border-radius: 4px; text-transform: uppercase; }}
  .trial-title {{ font-size: 19px; color: #0b192c; margin: 6px 0 2px 0; }}
  .trial-sub {{ color: #64748b; font-size: 13px; margin: 0; }}
  .status-badge {{ font-size: 12px; font-weight: 700; padding: 5px 12px; border-radius: 20px; text-transform: uppercase; display: inline-block; }}
  .badge-eligible {{ background: #dcfce7; color: #15803d; }}
  .badge-action {{ background: #fef9c3; color: #854d0e; }}
  .badge-ineligible {{ background: #fee2e2; color: #b91c1c; }}
  .conf-text {{ font-size: 13px; font-weight: 700; color: #0b192c; text-align: right; margin-top: 4px; }}
  .summary-box {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 6px; font-size: 14px; line-height: 1.5; }}
  .section-label {{ font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; color: #475569; margin: 18px 0 8px 0; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 16px; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }}
  th {{ background: #f8fafc; font-weight: 600; color: #334155; }}
  .chip {{ font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; display: inline-block; }}
  .chip-met {{ background: #dcfce7; color: #166534; }}
  .chip-unmet {{ background: #fee2e2; color: #991b1b; }}
  .chip-missing {{ background: #fef3c7; color: #92400e; }}
  .citation {{ font-style: italic; color: #64748b; font-size: 11px; }}
  .missing-box {{ background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 12px; font-size: 13px; color: #92400e; }}
  .missing-box ul {{ margin: 6px 0 0 18px; padding: 0; }}
  .footer {{ border-top: 1px solid #e2e8f0; margin-top: 40px; padding-top: 20px; font-size: 12px; color: #94a3b8; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Clinical Trial Eligibility Adjudication Report</h1>
    <div class="meta">GenAI Research Adjudication Platform &bull; {now_str} &bull; ID: <code>{patient_identifier}</code></div>
  </div>

  <div class="patient-card">
    <h2>Subject Clinical Summary</h2>
    <p><strong>Demographics:</strong> Age {demo.get('age', 'N/A')}, {demo.get('gender', 'N/A')}, ECOG PS: {demo.get('ecog_ps', 'N/A')}<br>
    <strong>Primary Diagnosis:</strong> {cond.get('primary_diagnosis', 'N/A')} ({cond.get('stage', 'N/A')}, {cond.get('histology', 'N/A')})<br>
    <strong>Biomarkers:</strong> {', '.join([f"{b.get('gene')}: {b.get('status')} ({b.get('details')})" for b in biomarkers]) or 'None recorded'}</p>
  </div>

  <h2>Adjudicated Trial Results ({len(matching_results)} Trials Evaluated)</h2>
  {cards_html}

  <div class="footer">
    Clinical Trial Eligibility Matcher &bull; For Clinical Research & Investigational Use Only
  </div>
</div>
</body>
</html>"""
    return html
