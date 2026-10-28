# Lead Intelligence System

**IIT Roorkee CEC – Forward Deployed Engineer Mini Project**

## 1. Project Overview

The Lead Intelligence System is a Python-based B2B sales lead qualification and outreach automation project.

It processes lead information from CSV files, evaluates leads using a transparent rule-based scoring system, prioritizes qualified prospects, and uses the Groq API to generate personalized sales outreach.

The project demonstrates data validation, deterministic decision-making, LLM integration, batch processing, error recovery, and structured reporting.

## 2. Key Features

- CSV ingestion and required-column validation
- Rule-based lead scoring on a 1–10 scale
- Lead classification into QUALIFIED, REVIEW, and REJECTED
- Priority ranking based on qualification and score
- Personalized outreach using Groq LLM
- Three outreach variants per qualified lead
- Batched API processing and response validation
- Retry handling for temporary API errors and invalid responses
- Checkpoint-based recovery for failed batches
- JSON reporting with aggregate statistics and lead-level results
- Automated tests for pipeline integration and recovery behavior

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Application development |
| pandas | CSV processing and lead analysis |
| Groq API | LLM-powered outreach generation |
| python-dotenv | Environment variable management |
| PyYAML | Configuration support |
| pytest | Automated testing |
| JSON | Structured output reporting |

## 4. Project Structure

```text
IITR_Lead_Intelligence_System/
├── leads.csv
├── main.py
├── rubric.py
├── llm_client.py
├── pipeline.py
├── report_generator.py
├── recovery.py
├── run_recovery.py
├── run_final_recovery.py
├── check_models.py
├── config.yaml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── data/
│   ├── leads_training.csv
│   ├── leads_testing.csv
│   └── leads_full_scale_100.csv
├── output/
│   └── output_report_final.json
└── tests/
    ├── test_batch_coordinator.py
    ├── test_outreach_recovery.py
    ├── test_pipeline_integration.py
    └── test_end_to_end_report.py
```

## 5. Input Dataset

The system expects a CSV file containing the following columns:

| Column | Description |
|---|---|
| name | Prospect's name |
| company | Organization name |
| company_size | Organization size category |
| industry | Business industry |
| source | Lead acquisition source |
| last_interaction_date | Date of the most recent interaction |

The submission includes a 100-lead dataset, exceeding the minimum requirement of 30 leads.

## 6. Lead Scoring and Qualification

The scoring engine evaluates each lead using five weighted factors.

| Factor | Maximum points |
|---|---:|
| Company size | 3.0 |
| Industry | 2.5 |
| Lead source | 2.0 |
| Interaction recency | 1.5 |
| Data completeness | 1.0 |
| **Total** | **10.0** |

Scores are constrained to the range 1–10.

### Qualification thresholds

- **QUALIFIED:** Score of 7 or higher
- **REVIEW:** Score from 4 to below 7
- **REJECTED:** Score below 4

Critical missing or invalid information can trigger manual review.

The system records scoring explanations and prioritizes qualified leads.

## 7. AI-Powered Outreach

Qualified leads are sent to the Groq API to generate three personalized outreach variants:

1. Professional email
2. Friendly email
3. LinkedIn message

The prompt uses available lead details such as name, company, and industry.

It instructs the LLM to avoid unsupported claims, invented statistics, unverified company achievements, and fabricated prior interactions.

The configured model is `openai/gpt-oss-20b`.

## 8. Reliability and Error Handling

The system includes:

- CSV schema validation
- Structured LLM response validation
- Retries for temporary Groq API failures
- Retries for incomplete or malformed LLM responses
- Batch-level failure isolation
- Recording of failed batches
- Targeted recovery of missing outreach
- Duplicate lead-ID prevention during recovery
- Separate recovery reports and backup files

A failed API batch does not require regenerating every successful outreach message.

## 9. Installation

### Prerequisites

- Python 3.12 or a compatible version
- Internet connectivity for Groq API requests
- A valid Groq API key

### Setup

Clone or extract the project, then open a terminal in its root directory.

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a `.env` file using `.env.example` as a reference.

Set your own credentials:

```dotenv
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

Never commit or distribute a real API key.

## 10. Running the Full Pipeline

From the project root, with the virtual environment activated and Groq configured, run:

```powershell
@'
from pipeline import run_and_export_pipeline

report = run_and_export_pipeline(
    csv_path="leads.csv",
    output_path="output/output_report.json",
    batch_size=5
)

print(report["summary"])
print("Outreach leads:", len(report["outreach_results"]))
print("Failed batches:", len(report["failed_batches"]))
'@ | python -
```

This executes CSV ingestion, lead scoring, qualification, prioritization, outreach generation, and JSON export.

Live execution consumes Groq API quota. The saved final report is included so evaluators can inspect the completed results without rerunning the API.

## 11. Recovery Workflow

If any outreach batches fail, the system can identify missing qualified leads and retry only those leads.

Recovery scripts used during development:

```powershell
python run_recovery.py
python run_final_recovery.py
```

The recovery process uses smaller batches and preserves completed outreach results.

These scripts use the saved report filenames configured in their source code. They are intended for recovering a previous run rather than starting a new one.

## 12. Automated Testing

Run the test suite:

```powershell
python -m pytest -q
```

The tests cover:

- Incomplete LLM response recovery
- Batch processing and failed-batch isolation
- Pipeline integration
- End-to-end JSON report generation with mocked outreach

Mocked tests do not require real Groq API requests.

## 13. Final Execution Results

The full-scale run processed 100 leads.

| Metric | Result |
|---|---:|
| Total leads processed | 100 |
| Qualified | 80 |
| Review | 19 |
| Rejected | 1 |
| Qualification percentage | 80% |
| Qualified leads with outreach | 80 |
| Outreach variants generated | 240 |
| Remaining failed batches | 0 |

The final report is stored in:

`output/output_report_final.json`

### Rejection analysis

The rejected lead had a score of 3.5/10. The reporting system identified the following contributing factors:

- Company size outside target
- Industry outside preferred segments
- Low engagement signal
- Older interaction

These explanations are derived from the rule-based scoring rubric.

## 14. Challenges and Solutions

**Challenge: Incomplete Groq responses**

The model occasionally returned fewer or more leads than requested.

**Solution:** Validate response structure, retry invalid outputs, and isolate failed batches.

**Challenge: Groq JSON validation errors**

Some API requests failed because the model could not produce valid JSON.

**Solution:** Record failed batches and recover missing leads through smaller requests.

**Challenge: Rate limiting**

Temporary rate-limit errors occurred during recovery.

**Solution:** Apply retry logic with delays.

**Challenge: Unsupported AI claims**

Early outreach examples contained unverified statements about prospect companies.

**Solution:** Strengthen prompt constraints to discourage fabricated company facts and require conditional benefit language.

**Challenge: Partial full-scale execution**

The initial 100-lead run generated outreach for only 55 qualified leads.

**Solution:** Preserve successful results, recover 23 additional leads in smaller batches, and recover the final two individually.

**Challenge: Misleading rejection reasons**

The initial summary counted positive scoring contributions as rejection reasons.

**Solution:** Classify relevant low-scoring factors into meaningful rejection categories.

## 15. Learning Outcomes

This project provided practical experience with:

- Building modular Python applications
- Data ingestion and validation
- Business-rule implementation
- Explainable scoring and decision systems
- Integrating an external LLM API
- Prompt engineering and hallucination mitigation
- Batch processing
- API retry and recovery strategies
- Idempotent result merging
- JSON reporting
- Automated testing
- Secure configuration management

## 16. Security and Limitations

- API credentials are stored in a local `.env` file and must not be included in submissions.
- LLM-generated outreach should be reviewed before sending to real prospects.
- The scoring rubric is a configurable business heuristic, not a trained predictive model.
- Qualification results depend on the selected scoring rules and evaluation date.
- The sample dataset and completed report are provided for demonstration and evaluation.

## 17. Conclusion

The Lead Intelligence System demonstrates a complete workflow from structured lead data to explainable qualification decisions and personalized outreach.

The final execution successfully scored 100 leads and produced 240 outreach variants for all 80 qualified leads, using recovery mechanisms to resolve partial API failures without repeating completed work.
