# Status

Live checklist of what is left to complete on this project, in the same checkbox
format the portfolio tracking dashboard reads. Check a box (`[ ]` -> `[x]`) as
you finish.

> Project: **GENIE BPC BrCa Brain-Metastasis Analysis** · Stage: **data / modeling**
> Cohort: GENIE BPC BRCA.

## 1. Scoping
- [x] Aims written with per-aim cohort restriction (see README §1)
- [x] Primary outcome defined (CNS metastasis ever)

## 2. Data collection & processing
- [ ] Run the ETL: harmonize scripts never executed; `data/processed/` empty (all Aims depend on it)
- [x] Implement `src/data collection and processing/add_pathways_genie_bpc.R` (gene-binary + Sanchez-Vega pathways via gnomeR; not yet run on real data)
- [x] Raw GENIE BPC release landed in `data/raw/` (git-ignored)
- [ ] Missingness audit finalized on the GENIE BPC analytic frame

## 3. Exploratory data analysis
- [x] Aim 1 gene-prevalence tables + oncoprint/forest (GENIE)

## 4. Modeling
- [ ] Generate missing outputs: all Aim 2 & 3 survival / XGBoost-AFT result tables
- [ ] Sensitivity checks on the fitted survival / ML models

## 5. Reporting & repo hygiene
- [x] Add requirements.txt / environment.yml with pinned versions (Python `requirements.txt` + conda `environment.yml` added; R `renv.lock` still pending)
- [ ] Flesh out root README with setup + pipeline run order
- [x] Move/archive AI-workflow tutorial folders cluttering the research repo (-> `archive/`)
- [ ] Publication figures finalized in `reports/figures/`
- [ ] Reproducibility check: fresh clone runs the pipeline end-to-end
