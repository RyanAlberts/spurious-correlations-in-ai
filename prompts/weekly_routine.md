# Weekly routine — Spurious Correlations in AI

You are running the weekly maintenance pass for the *Spurious Correlations in AI* repo.
Today is the scheduled Saturday run. Work autonomously and commit to `main`.

## Steps

1. **Refresh the data + analysis.** Run:
   ```
   python -m spurcorr.pipeline --notes "weekly $(date +%F)"
   ```
   (Add `--offline` only if the network is restricted.) This re-collects every reachable
   source, recomputes correlations/ITS/clusters, regenerates `docs/charts/`, writes a new
   `data/catalog/catalog-<date>.json` snapshot, and rebuilds `README.md`.

2. **Discover new candidate terms.** Use `spurcorr.tools.discover_candidates` against the
   Kobak excess list to surface up to ~10 new *style* words we aren't tracking yet. Add the
   most promising to `data/ai_vocabulary.yaml` (with a cluster + sensible wiki/wiktionary
   titles). Prefer non-obvious turns of phrase over obvious content words.

3. **Review the flagged findings** (see VALIDATION.md):
   - Eyeball 2–3 `candidate-causal` charts: is there a real post-release break, or just a
     pre-existing trend? Note your call.
   - If any **negative control** shows AI-like excess (`control-anomaly`), STOP and flag it —
     the method may be broken this week. Do not publish without investigating.
   - **Do not** introduce or publish any correlation that leaves the language /
     search-frequency domain without explicit owner approval (use AskUserQuestion).

4. **Commit to `main`** with a message summarising the run, e.g.:
   `weekly 2026-06-06: 24 terms, 19 candidate-causal; added "burgeoning","tapestry";
   validated delve/showcasing; flagged none.`
   Commit `README.md`, `docs/charts/`, `data/catalog/`, and any vocab additions.

5. **Check the "is our list working?" gate.** If candidates have held up and controls have
   stayed null for several weeks, leave a note in the commit / an issue proposing we start
   the fast-follow backlog (BACKLOG.md): the AI-tell de-slopper tool (B1) and the viral
   social workflow (B2).

Keep it tight. The PR diff / commit is the record — don't over-narrate.
