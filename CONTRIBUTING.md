# Contributing

Thanks for poking at *Spurious Correlations in AI*. A few ground rules that keep the
project honest and lightweight.

## Principles

- **Real data only.** A collector must return measured values with provenance. The
  pipeline refuses to publish synthesised/placeholder series (`SeriesResult.real`).
- **Free by default.** Prefer free, no-key sources. Paid options are documented in
  BACKLOG.md, not wired into the core.
- **Spurious until proven otherwise.** New analysis should make it *harder* to call a
  correlation causal, not easier. Add confounds and controls, not just prettier charts.
- **Lightweight deps.** `pandas/numpy/scipy/matplotlib/ruptures/requests/pyyaml`. No
  heavyweight ML/orchestration frameworks.

## Adding a data source

1. Create `src/spurcorr/collectors/<name>.py` with a `Collector` subclass implementing
   `available()` (probe the host) and `collect(term_cfg) -> SeriesResult | None`.
2. Register it in `collectors/__init__.py::REGISTRY` and (if it should be preferred as the
   primary series) in `pipeline.py::PRIMARY_PREFERENCE`.
3. Add a no-network test in `tests/` (inject a tiny fixture; don't hit the live API in CI).

## Adding tracked terms

Edit `data/ai_vocabulary.yaml`. Include a `cluster`, and `wiki`/`wiktionary`/`gdelt_query`
lookups. For the reproducible PubMed anchor to chart it, set `pubmed_word` to a single
token present in the Kobak matrix. Mark `negative_control: true` for words that should
show no AI signal.

## Dev loop

```
pip install -e ".[dev]"
python -m spurcorr.pipeline --offline   # fast, reproducible run on the PubMed anchor
pytest -q
ruff check src tests
```

## Attribution

Over-representation ratios come from GPTZero's published list and from Kobak et al. (2025)
and Liang et al. (2024). Cite them; don't pass their numbers off as ours. This project is
not affiliated with GPTZero or Tyler Vigen.
