"""Price table: model -> per-token cost, loaded from bundled YAML (user-overridable)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_DEFAULT_KEY = "default"


@dataclass(frozen=True)
class ModelPrice:
    input_per_token: float  # USD per single input token
    output_per_token: float


class PriceTable:
    """Case-insensitive model -> ModelPrice lookup with a `default` fallback.

    YAML values are USD per 1,000,000 tokens; stored internally per-token.
    """

    def __init__(self, prices: dict[str, ModelPrice], default: ModelPrice):
        self._prices = prices
        self._default = default

    @classmethod
    def from_yaml(cls, path: str | Path) -> PriceTable:
        raw = yaml.safe_load(Path(path).read_text()) or {}
        if _DEFAULT_KEY not in raw:
            raise ValueError(f"price table {path} must define a `{_DEFAULT_KEY}` entry")

        def to_price(entry: dict) -> ModelPrice:
            return ModelPrice(
                input_per_token=float(entry["input"]) / 1_000_000,
                output_per_token=float(entry["output"]) / 1_000_000,
            )

        default = to_price(raw[_DEFAULT_KEY])
        prices = {
            name.lower(): to_price(entry)
            for name, entry in raw.items()
            if name != _DEFAULT_KEY
        }
        return cls(prices, default)

    def lookup(self, model: str) -> ModelPrice:
        return self._prices.get((model or "").lower(), self._default)

    def cost_usd(self, model: str, input_tokens: int, output_tokens: int) -> float:
        p = self.lookup(model)
        return input_tokens * p.input_per_token + output_tokens * p.output_per_token
