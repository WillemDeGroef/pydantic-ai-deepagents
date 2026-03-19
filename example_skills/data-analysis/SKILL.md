---
name: data-analysis
description: Structured data analysis workflow. Use when asked to analyse data, find patterns, generate insights, or produce data-driven reports from CSV, JSON, or other structured data.
license: MIT
---

# Data Analysis Skill

## When to Use

Activate this skill when the user asks you to:
- Analyse a dataset (CSV, JSON, or other structured data)
- Find patterns, trends, or anomalies in data
- Generate statistical summaries or insights
- Produce a data-driven report or visualisation plan

## Workflow

### Step 1: Understand the data

1. Read the data file(s) with `read_file`
2. Write an initial data profile to `data_profile.md`:
   - Number of rows/records
   - Column names and inferred types
   - Sample values (first 5 rows)
   - Obvious data quality issues (nulls, inconsistencies)
3. Ask clarifying questions if the analysis goal is unclear

### Step 2: Clean and prepare

If data quality issues exist:
1. Document issues in `data_cleaning_log.md`
2. Write a cleaned version to a new file
3. Note any records dropped or values imputed

### Step 3: Analyse

Use the analysis script template in `scripts/analysis_template.py` if
shell execution is available. Otherwise, perform analysis manually:

1. **Descriptive statistics** — counts, means, medians, distributions
2. **Comparisons** — group-by analysis, cross-tabulations
3. **Trends** — time-series patterns, growth rates
4. **Anomalies** — outliers, unexpected patterns

Write intermediate findings to `analysis_findings.md`.

### Step 4: Synthesise and report

1. Read back all findings files
2. Write a final report to `data_analysis_report.md`:
   - Executive summary (3-5 bullet points)
   - Methodology
   - Key findings with supporting numbers
   - Limitations and caveats
   - Recommendations

## Guidelines

- Always show your numbers — don't just say "increased", say "increased 23%"
- Note sample sizes and statistical significance where relevant
- Separate observations (what the data shows) from interpretations (what it means)
- Flag any assumptions you made during the analysis
