# The honesty framing: drift, not truth

This is non-negotiable and baked into all Vitals copy, dashboards, and the demo script.

## What Vitals measures

Vitals' online quality scores are **deviation from an established good baseline**, not
absolute correctness. Vitals answers:

> *Did quality change, when, and with which release?*

It does **not** answer *"is this answer true?"* No reference-free metric can, on
production traffic that has no golden answers.

## Why this is the right question

Every silent-regression incident in the wild is a *change* story, not a *truth* story:

- Anthropic confirmed Claude Code quality complaints were caused by product-layer
  prompt/reasoning changes — no model version change, no notification, and no way to
  detect it without measuring outputs. Engineers found out through user complaints.
- Prompt updates drive most LLM production incidents; provider model updates shift
  behavior with regressions undetected until users complain.

In all of these, the answer wasn't "objectively false" — it was **different from what
had been working**. That is exactly the signal drift detection captures, and it fires
before the complaints arrive.

## How we avoid over-claiming

- **Reference-free online metrics.** Drift (PSI vs a rolling healthy baseline),
  self-consistency, and output stability run without golden answers. Reference-based
  absolute scoring exists only against the seeded eval set in the demo, and is disclosed
  as such.
- **Never emit a score you can't stand behind.** During baseline warming the signal is
  `warming` — no score. A clean-run false positive is treated as worse than slow
  detection (spike S4 runs with a zero false-positive budget on clean traffic).
- **CUSUM gives onset, not blame.** We report *when* sustained drift began. Attributing
  *which pipeline component* drifted (PELT) is deferred to V2 and not claimed in V1.

## What this buys us in expert review

Over-claiming correctness is how this product dies in front of judges who know the
space. Leading with "we measure change, and change is the incident" is both honest and
the stronger claim: it is the signal that the entire cited body of evidence is about.
