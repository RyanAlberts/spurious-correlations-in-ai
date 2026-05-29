# Scheduling the weekly run (Saturdays)

The pipeline is designed to run **every Saturday**, refresh the charts + catalog, and
commit the result **directly to `main`**. Three ways to schedule it — pick one (GitHub
Actions is the autonomous default).

## 1. GitHub Actions (recommended, autonomous)

`.github/workflows/weekly.yml` runs `cron: '0 14 * * 6'` (Saturday 14:00 UTC), executes
the pipeline, and commits refreshed `README.md`, `docs/charts/`, and `data/catalog/`
straight to `main` using the built-in Actions bot. Nothing to install — it just needs
the repo's default `GITHUB_TOKEN` write permission (set in the workflow).

To run it on demand: **Actions → "weekly" → Run workflow**.

## 2. Terminal cron (local fallback)

```cron
# crontab -e  — Saturday 09:00 local; runs pipeline then commits to main
0 9 * * 6  cd /path/to/spurious-correlations-in-ai && \
  /usr/bin/python3 -m spurcorr.pipeline >> run.log 2>&1 && \
  git add -A && git commit -m "weekly: $(date +%F)" && git push origin main
```

Optionally add a curation pass with Claude after the data run:

```cron
0 10 * * 6  cd /path/to/spurious-correlations-in-ai && \
  claude -p "$(cat prompts/weekly_routine.md)" >> curate.log 2>&1
```

## 3. Claude Code recurring session (desktop / web) — the "routine prompt"

`prompts/weekly_routine.md` is a reusable prompt that re-runs the pipeline, reviews newly
flagged correlations, holds anything outside the language/search-frequency domain for
your review, updates the catalog + README, and commits to `main`.

- **Desktop / web app**: start a session in this repo and paste the routine prompt (or
  use a scheduled/triggered session if available on your plan — see
  https://code.claude.com/docs/en/claude-code-on-the-web). Set it to repeat weekly.
- **`/loop` (interactive)**: in a Claude Code session you can run
  `/loop 7d /weekly_routine` style recurring tasks.

## Manual data you may want to drop in first

The live web collectors run wherever their hosts are reachable. To add sources that have
no free API, place exports under `data/manual/` before the run:

- `data/manual/google_trends/<term>.csv` — Google Trends "Interest over time" CSV export
- `data/manual/linkedin/<term>.csv` — columns `date,value` (LinkedIn Premium search)
- `data/manual/openrouter/snapshot.csv` — columns `date,model,tokens`

`<term>` is the lower-cased, underscore-slugged term (e.g. `a_nuanced_understanding`).
