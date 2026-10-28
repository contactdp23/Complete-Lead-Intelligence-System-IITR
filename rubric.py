
from datetime import date, datetime
import pandas as pd


def is_missing(value):
    """Check whether a field is missing or blank."""
    if pd.isna(value):
        return True
    return isinstance(value, str) and not value.strip()


def qualify_lead(lead, evaluation_date=None):
    """Score one lead using a five-factor rubric."""

    if evaluation_date is None:
        evaluation_date = date.today()

    score = 0.0
    reasons = []
    review_flags = []

    # 1. Company size (maximum 3 points)
    size = pd.to_numeric(
        lead.get("company_size"), errors="coerce"
    )

    if pd.isna(size) or size <= 0:
        review_flags.append("Missing or invalid company size")
    elif 20 <= size <= 500:
        score += 3.0
        reasons.append("Company size matches target ICP (+3)")
    elif 501 <= size <= 2000:
        score += 2.0
        reasons.append("Company is above preferred size (+2)")
    elif 10 <= size < 20:
        score += 1.5
        reasons.append("Company is smaller than target (+1.5)")
    else:
        score += 0.5
        reasons.append("Company size is outside target (+0.5)")

    # 2. Industry fit (maximum 2.5 points)
    industry = str(lead.get("industry", "")).strip().lower()

    core = {"saas", "technology", "software", "fintech"}
    secondary = {
        "finance", "healthcare", "logistics",
        "retail", "edtech"
    }

    if is_missing(lead.get("industry")):
        review_flags.append("Missing industry")
    elif industry in core:
        score += 2.5
        reasons.append("Core target industry (+2.5)")
    elif industry in secondary:
        score += 1.5
        reasons.append("Secondary target industry (+1.5)")
    else:
        score += 0.5
        reasons.append("Industry outside preferred segments (+0.5)")

    # 3. Lead source (maximum 2 points)
    
    # 3. Lead source (maximum 2 points)
    source_value = lead.get("source")

    source = (
        str(source_value).strip().lower()
        if not is_missing(source_value)
        else ""
    )

    if not source:
        review_flags.append("Missing lead source")

    elif source in {"inbound demo request", "referral"}:
        score += 2.0
        reasons.append("Strong acquisition signal (+2)")

    elif source in {"sales call", "webinar attendee"}:
        score += 1.5
        reasons.append("Moderate engagement signal (+1.5)")

    elif source in {"linkedin outreach", "content download"}:
        score += 1.0
        reasons.append("Early engagement signal (+1)")

    else:
        reasons.append("Low or unrecognized acquisition signal (+0)")

    # 4. Engagement recency (maximum 1.5 points)
    raw_date = lead.get("last_interaction_date")

    try:
        interaction = datetime.strptime(
            str(raw_date).strip(), "%Y-%m-%d"
        ).date()
        days = (evaluation_date - interaction).days

        if days < 0:
            review_flags.append("Future interaction date")
        elif days <= 30:
            score += 1.5
            reasons.append("Recent interaction (+1.5)")
        elif days <= 90:
            score += 1.0
            reasons.append("Interaction within 90 days (+1)")
        elif days <= 180:
            score += 0.5
            reasons.append("Interaction within 180 days (+0.5)")
        else:
            reasons.append("Stale interaction (+0)")
    except (ValueError, TypeError):
        review_flags.append("Missing or invalid interaction date")

    # 5. Data completeness (maximum 1 point)
    fields = [
        "name", "company", "company_size",
        "industry", "source", "last_interaction_date"
    ]

    present = sum(
        not is_missing(lead.get(field))
        for field in fields
    )

    if present == 6:
        score += 1.0
        reasons.append("Complete lead record (+1)")
    elif present == 5:
        score += 0.5
        reasons.append("Mostly complete lead record (+0.5)")
    else:
        reasons.append("Incomplete lead record (+0)")

    if is_missing(lead.get("name")):
        review_flags.append("Missing contact name")

    if is_missing(lead.get("company")):
        review_flags.append("Missing company name")

    # Score must remain between 1 and 10
    score = round(max(1.0, min(score, 10.0)), 1)

    # Human review takes precedence for uncertain records
    if review_flags:
        decision = "REVIEW"
    elif score >= 7:
        decision = "QUALIFIED"
    elif score >= 4:
        decision = "REVIEW"
    else:
        decision = "REJECTED"

    return {
        "score": score,
        "decision": decision,
        "reasoning": reasons,
        "review_flags": review_flags
    }
