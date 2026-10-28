
from datetime import date

from main import load_leads, score_leads, rank_leads
from llm_client import split_into_batches, generate_outreach_for_all
from report_generator import export_json_report


def prepare_outreach_pipeline(
    csv_path,
    evaluation_date=date(2024, 1, 21),
    batch_size=5
):
    """Load, score, rank, and prepare qualified leads for outreach."""

    leads_df = load_leads(csv_path)

    scored_df = score_leads(
        leads_df,
        evaluation_date=evaluation_date
    )

    ranked_df = rank_leads(scored_df)

    qualified_df = ranked_df[
        ranked_df["decision"] == "QUALIFIED"
    ].copy()

    qualified_records = qualified_df.to_dict(
        orient="records"
    )

    batches = split_into_batches(
        qualified_records,
        batch_size=batch_size
    )

    return {
        "ranked_df": ranked_df,
        "qualified_records": qualified_records,
        "batch_count": len(batches)
    }

def run_outreach_pipeline(
    csv_path,
    evaluation_date=date(2024, 1, 21),
    batch_size=5
):
    """Score leads and generate outreach for qualified leads."""

    prepared = prepare_outreach_pipeline(
        csv_path=csv_path,
        evaluation_date=evaluation_date,
        batch_size=batch_size
    )

    outreach = generate_outreach_for_all(
        qualified_leads=prepared["qualified_records"],
        batch_size=batch_size
    )

    return {
        "ranked_df": prepared["ranked_df"],
        "outreach_results": outreach["results"],
        "failed_batches": outreach["failed_batches"]
    }

def run_and_export_pipeline(
    csv_path,
    output_path="output/output_report.json",
    evaluation_date=date(2024, 1, 21),
    batch_size=5
):
    """Run lead intelligence pipeline and export the JSON report."""

    pipeline_result = run_outreach_pipeline(
        csv_path=csv_path,
        evaluation_date=evaluation_date,
        batch_size=batch_size
    )

    report = export_json_report(
        ranked_df=pipeline_result["ranked_df"],
        output_path=output_path,
        outreach_results=pipeline_result["outreach_results"],
        failed_batches=pipeline_result["failed_batches"]
    )

    return report
