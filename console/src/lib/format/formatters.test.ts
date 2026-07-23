import { describe, expect, it } from "vitest";
import { formatCurrency } from "./currency";
import { formatDuration } from "./duration";
import { formatNumber } from "./number";
import { formatRelativeTime } from "./relativeTime";
import { formatSigma } from "./sigma";
import { formatExcerpt, truncateId } from "./truncate";

describe("§13 Formatters", () => {
  it("formatSigma handles signed minus sign, flat below 1σ, and em dash null", () => {
    expect(formatSigma(4.2)).toBe("+4.2σ");
    expect(formatSigma(-0.3)).toBe("−0.3σ flat"); // U+2212 minus sign & flat
    expect(formatSigma(0.4)).toBe("+0.4σ flat");
    expect(formatSigma(null)).toBe("—"); // U+2014 em dash
  });

  it("formatCurrency formats 4 decimals under $1 and 2 decimals above $1", () => {
    expect(formatCurrency(0.0042)).toBe("$0.0042");
    expect(formatCurrency(1.28)).toBe("$1.28");
    expect(formatCurrency(null)).toBe("—");
  });

  it("formatNumber formats thousands separator", () => {
    expect(formatNumber(1240)).toBe("1,240");
    expect(formatNumber(null)).toBe("—");
  });

  it("formatDuration formats seconds, minutes, and hours", () => {
    expect(formatDuration(90)).toBe("90s");
    expect(formatDuration(150)).toBe("2m 30s");
    expect(formatDuration(3840)).toBe("1h 04m");
    expect(formatDuration(null)).toBe("—");
  });

  it("truncateId and formatExcerpt format IDs and text excerpts", () => {
    expect(truncateId("4f2a91b8e301")).toBe("4f2a91…");
    expect(formatExcerpt("Hello world")).toBe('"Hello world"');
  });
});
