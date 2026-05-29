# Backlog

Prioritised follow-ups. v1 priority is a **great dataset from free proxies**; we scale
up only if the first month of weekly runs looks good. Nothing here is built yet.

## Gated on "is our list working?" (review after ~1 month of weekly runs)

### B1 — AI-tell "de-slopper" tool for the owner's AI agents  ⭐ (owner request)
Build a tool that scans any written deliverable for words/phrases this project finds to
be **over-represented in AI by ≥10×**, and rewrites them into more common, human
phrasing (e.g. "delve into" → "look at"; "a nuanced understanding" → "a good grasp";
strip reflexive em-dashes). 

- **Source of truth**: the over-representation catalog produced here (GPTZero top-100 +
  our `candidate-causal` terms), filtered to ratio ≥ 10×.
- **Policy (to adopt once the list proves out)**: make it a **must-use** pre-send step
  whenever the owner drafts LinkedIn posts, social copy, emails, or any human-facing
  text. Goal: deliberately *not* sound like AI.
- **Status**: do **not** wire up yet. Revisit once we trust the list (i.e. controls stay
  null and candidates survive review for a few weeks). Then ship as a small library +
  an agent tool, and add the "must-use" rule to the owner's drafting workflow.
- **Risk to watch**: over-correction (rewrites that flatten voice); keep a human in the loop.

## Fast-follow after ~1 month (only if results are compelling)

### B2 — Viral social workflow
A Claude workflow turning each week's findings into IG / TikTok / Twitter posts:
hook + transcript, short **video (Google AI Pro / Veo)**, and sound. Lead with the most
shareable correlation (big *r*, surprising word).

### B3 — Concept-cluster campaign implications
Interpret what each rising concept cluster (academic-hedging, promotional, …) means for
messaging; choose the clusters/words with the best narrative for B2.

### B4 — Cross-domain spurious correlations (classic Tyler-Vigen)
Pair AI-vocabulary trends with absurd unrelated series for comedic effect. **Owner-gated**:
anything outside language/search-frequency must be reviewed before publishing.

### B5 — LinkedIn computer-use automation
Owner has LinkedIn Premium. A local Playwright/computer-use script to pull LinkedIn post
search frequency for tracked terms (cannot run in the restricted CI sandbox). Non-critical.

## Data & infra

- **B6 — Paid options ROI review**: start with Brand24 (~$199/mo, by-model AI mention
  tracking). Evaluate vs free proxies once volume justifies it. SerpApi/Glimpse/X-API: skip.
- **B7 — Interactive GitHub Pages site**: Plotly dual-axis charts + "discover a random
  correlation", closer to tylervigen.com. v1 is README + static charts by choice.
- **B8 — More live sources**: Reddit Arctic Shift, PyPI/npm SDK downloads, GitHub stars,
  Chatbot Arena vote dataset (HF) — all blocked in the current sandbox; enable in CI.
- **B9 — Data-driven clustering**: KMeans/t-SNE on word trajectories to discover clusters
  beyond the curated taxonomy.
- **B10 — GPTZero live parser**: when the page is reachable, parse the DOM to refresh
  ratios automatically (currently a best-effort reachability probe + YAML snapshot).
