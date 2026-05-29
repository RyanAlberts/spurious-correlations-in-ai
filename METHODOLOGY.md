# Methodology

This project asks a deliberately mischievous question — *is "delve" an AI word?* —
and then refuses to answer it with a correlation coefficient alone. Here is exactly
what the pipeline computes and why.

## 1. The two series

For each tracked term we build:

- **Word interest** — a time series of how much the word/phrase shows up in human
  output. Sources (whichever are reachable): PubMed abstract frequency (Kobak et al.,
  yearly, our reproducible anchor), Wikipedia & Wiktionary pageviews (daily), GDELT
  news-article volume, Hacker News mentions, and manually-exported Google Trends.
- **Cumulative model releases** — a monotone step function counting public AI model
  releases up to each date (`data/model_releases.yaml`).

## 2. The hook: correlation

We report Pearson and Spearman correlation between the word series and the cumulative-
release series. This is the Tyler-Vigen move — and it is almost worthless on its own,
because *any* two series that both rise after 2022 will correlate near +1. We show it,
then immediately try to break it.

## 3. The discriminating test: interrupted time series (ITS)

The real question is whether a word **broke away from its own prior trend** after a
release. We fit a log-linear trend on each word's pre-release history (before the
landmark anchor, ChatGPT / 2022‑11‑30), extrapolate it forward, and measure the
**excess ratio** = mean(observed / counterfactual) over the post-release window.

- An AI word like `delve` shows excess ≈ 6× — it vastly exceeds its own pre-2022 trend.
- A control word like `Saturday` shows excess ≈ 0.9× — bang on its own trend.

Because every word is judged against *itself*, "everything went up in 2023" is
controlled for per-word. This mirrors the excess-frequency method of Kobak et al. (2025).

## 4. Confound control: partial correlation

We additionally partial out a **control series** (the averaged, z-scored trajectory of
the negative-control words) from the word/release correlation. A term whose correlation
survives is a stronger candidate; one that collapses was riding shared drift.

## 5. Diffusion lag (hypothesis H1)

We cross-correlate the word against the release series at lags 0…3 steps and report the
lag maximising correlation. A non-negative best lag is consistent with usage diffusing
*after* releases.

## 6. The verdict

A term is **`candidate-causal`** only if: strong correlation **and** a real post-release
ITS excess **and** survival of the confound control. It is then **flagged for human
review** before we believe it. Otherwise it is **`spurious`** (the honest default) or
**`inconclusive`**. A negative control that lights up is a **`control-anomaly`** — a
signal that the *method* is broken, not that umbrellas are an AI plot.

## 7. Hypotheses tracked

- **H1 Diffusion lag** — interest rises after release, with a lag.
- **H2 Stylistic markers** — em-dashes, "it's not just X, it's Y", etc. (corpus collectors).
- **H3 Definition-seeking** — Wiktionary lookups (people looking a word *up*), possibly
  leading mainstream usage.
- **H4 Backlash inflection** — once a word is a known AI tell, human usage may *decline*.
- **H5 Cross-model synchrony** — rises around *multiple* labs' releases beat single-lab ties.

## 8. Honest limitations

- **Yearly granularity** for the PubMed anchor: enough to see the post-ChatGPT break,
  too coarse for fine lead-lag. Daily collectors (Wikipedia/GDELT) sharpen this where
  reachable.
- **English / biomedical bias** in the anchor corpus.
- **True per-model token usage is proprietary**; "engagement" uses proxies.
- **GDELT only retains ~3 months**, so it is a forward signal we snapshot weekly, not a
  back-test source.
- Correlation is not causation. We never claim otherwise; we just rank how hard a given
  correlation tried to fool us.
