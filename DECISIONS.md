# DECISIONS

Deviations from `PROJECT_PLAN.md` (the frozen source of truth), one line each with
rationale. The plan wins unless a decision here supersedes it.

- **Vitals embeds its own light OTLP receiver** rather than reusing spanIQ's
  `monitor/collectors/otel.py`. This is spike S1's documented fallback and keeps the
  Vitals layer self-contained and demo-reproducible; spanIQ stays unmodified.
- **spanIQ is vendored as source** (`spaniq/`, copied from `github.com/furyfist/spanIQ`
  v0.4.0) not pip-installed, per plan §11.3 (vendor preferred for reproducibility).
- **Core quality path uses ResponseDrift + CUSUM only** (numpy-pure), so the never-cut
  signal runs without the heavy `sentence-transformers` install. Consistency/stability
  (embedding-based) are optional (`vitals[quality-full]`) — matches the descope ladder.
- **Receiver default ports 4327/4328** to avoid colliding with SigNoz ingest on
  4317/4318 when both run on the same host.
