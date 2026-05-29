# Validation & human review

The pipeline never promotes a finding to "true" on its own. Anything labelled
`candidate-causal`, `control-anomaly`, or otherwise marked `needs_review` is held for a
human (or a second AI) to sign off before it carries weight.

## What to review each week

1. **Candidate-causal terms** — does the chart actually show a post-release break, or is
   it a long pre-existing trend the ITS happened to flatter? Sanity-check 2–3 by eye.
2. **Control anomalies** — a negative control (`umbrella`, `bicycle`, `Saturday`) showing
   AI-like excess means the *method* slipped. Investigate before trusting that week's run.
3. **Out-of-domain relations** — per project scope, any correlation that leaves the
   language / search-frequency world is automatically `needs_review` and must be approved
   by the project owner before publishing.
4. **OCR-suspect vocabulary** — entries flagged in `data/gptzero_vocabulary.yaml`
   (`a serf reminder` → `a stark reminder`, etc.). Confirm corrections against the live
   GPTZero list when it is reachable.

## Using your own tools to validate

- **Gemini Deep Research** (you have Gemini AI Pro): paste a candidate term + its chart
  and ask it to find independent evidence the word rose post-ChatGPT, and to argue the
  *spurious* case. If it can't refute it, the candidate is stronger.
- **Spot-check release dates** in `data/model_releases.yaml` against official blogs.

## Recording a decision

The catalog stores `needs_review` per term per run. When you accept/reject a candidate,
note it in the run's commit message (e.g. `validated: delve, showcasing; rejected: realm
(pre-2022 trend)`). Over time this builds an auditable trail of which words we believe
are genuinely AI-influenced.
