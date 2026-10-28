import json
from pathlib import Path
from collections import Counter


def export_json_report(ranked_df, output_path):
    """Export qualification summary and ranked leads to JSON."""

    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report = {
        "summary": generate_summary(ranked_df),
        "leads": ranked_df.to_dict(orient="records")
    }

    with output_file.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False,
            default=str
        )

    print(f"Report successfully saved to: {output_file}")

    return report

def generate_summary(ranked_df):
    """Generate aggregate lead qualification statistics."""

    total = len(ranked_df)

    decisions = ranked_df["decision"].value_counts()

    qualified = int(decisions.get("QUALIFIED", 0))
    review = int(decisions.get("REVIEW", 0))
    rejected = int(decisions.get("REJECTED", 0))

    qualification_percentage = (
        round((qualified / total) * 100, 2)
        if total > 0
        else 0.0
    )

    rejection_reasons = Counter()

    for _, lead in ranked_df.iterrows():
        if lead["decision"] == "REJECTED":
            for reason in lead["reasoning"]:
                rejection_reasons[str(reason)] += 1

    return {
        "total_leads": total,
        "qualified": qualified,
        "review": review,
        "rejected": rejected,
        "qualified_percentage": qualification_percentage,
        "common_rejection_reasons": dict(
            rejection_reasons.most_common(5)
        )
    }
