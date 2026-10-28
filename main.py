from datetime import date
from rubric import qualify_lead
import pandas as pd
from pathlib import Path

REQUIRED_COLUMNS = [
    "name",
    "company",
    "company_size",
    "industry",
    "source",
    "last_interaction_date",
]


def load_leads(file_path):
    """Read a CSV file and validate its structure."""

    path = Path(file_path)

    # Check whether the file exists
    if not path.is_file():
        raise FileNotFoundError(
            f"CSV file not found: {file_path}"
        )

    # Read the CSV
    df = pd.read_csv(path)

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()

    # Check for required columns
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Check for an empty dataset
    if df.empty:
        raise ValueError("CSV contains no lead records.")

    print(f"Successfully loaded {len(df)} leads.")
    print("All required columns are present.")

    return df


def score_leads(df, evaluation_date):
    """Apply the qualification rubric to every lead."""

    results = []

    for lead in df.to_dict(orient="records"):
        qualification = qualify_lead(
            lead,
            evaluation_date=evaluation_date
        )

        results.append({
            "name": lead.get("name"),
            "company": lead.get("company"),
            "score": qualification["score"],
            "decision": qualification["decision"],
            "reasoning": qualification["reasoning"],
            "review_flags": qualification["review_flags"]
        })

    return pd.DataFrame(results)



def rank_leads(scored_df):
    """Rank leads by qualification decision and score."""

    priority_order = {
        "QUALIFIED": 0,
        "REVIEW": 1,
        "REJECTED": 2
    }

    ranked = scored_df.copy()

    ranked["_decision_order"] = ranked["decision"].map(
        priority_order
    )

    ranked["_company_sort"] = (
        ranked["company"].fillna("").astype(str).str.lower()
    )

    ranked["_name_sort"] = (
        ranked["name"].fillna("").astype(str).str.lower()
    )

    ranked = ranked.sort_values(
        by=[
            "_decision_order",
            "score",
            "_company_sort",
            "_name_sort"
        ],
        ascending=[True, False, True, True],
        kind="stable"
    ).reset_index(drop=True)

    ranked["priority_rank"] = range(1, len(ranked) + 1)

    ranked = ranked.drop(
        columns=[
            "_decision_order",
            "_company_sort",
            "_name_sort"
        ]
    )

    return ranked




if __name__ == "__main__":
    leads = load_leads("data/leads_training.csv")

    scored = score_leads(
        leads,
        evaluation_date=date(2024, 1, 21)
    )

    print("\nLEAD QUALIFICATION RESULTS:")
    print(
        scored[
            ["name", "company", "score", "decision"]
        ].to_string(index=False)
    )

    print("\nDECISION SUMMARY:")
    print(scored["decision"].value_counts())

