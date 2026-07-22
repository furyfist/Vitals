# Vitals sidecar image. Includes the full quality path (spanIQ embedding metrics),
# so builds are heavier but the demo is reproducible out of the box.
FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal; numpy/scipy/torch ship manylinux wheels.
RUN pip install --no-cache-dir --upgrade pip

# Dependency layer first for cache friendliness.
COPY pyproject.toml README.md ./
COPY vitals/ ./vitals/
COPY spaniq/ ./spaniq/

# rich + sentence-transformers are spanIQ runtime deps (quality path).
RUN pip install --no-cache-dir . rich sentence-transformers

COPY vitals.yaml ./vitals.yaml

# Receiver (collector fan-out target). Emits out-of-band to SIGNOZ_OTLP_ENDPOINT.
EXPOSE 4327 4328

ENTRYPOINT ["vitals", "run"]
