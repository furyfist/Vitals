"""Server-rendered HTML console using Python f-strings and inline CSS (spec §9)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from vitals import __version__
from vitals.verdict.types import Verdict, VerdictState

STATE_COLORS = {
    "warming": "#6b7280",  # grey
    "steady": "#22c55e",  # green
    "changed": "#f59e0b",  # amber (not red!)
    "inconclusive": "#3b82f6",  # blue
}


def render_meter_bar(z: float | None, max_blocks: int = 16) -> str:
    """Render meter bar for sigma values: e.g. ████████████░░░░░░."""
    if z is None:
        return "░" * max_blocks
    abs_z = min(abs(z), 6.0)
    filled = int(round((abs_z / 6.0) * max_blocks))
    filled = max(1 if abs_z > 0 else 0, min(max_blocks, filled))
    return "█" * filled + "░" * (max_blocks - filled)


def render_console_html(
    latest_verdict: Verdict | None,
    verdict_feed: list[Verdict],
    scopes: list[dict[str, Any]],
    health_snapshot: dict[str, float],
    start_time: float,
) -> str:
    """Render the full single-screen Vitals console HTML."""
    state_str = latest_verdict.state.value if latest_verdict else "warming"
    accent_color = STATE_COLORS.get(state_str, "#6b7280")

    # Zone 1: Hero Verdict Card
    if latest_verdict:
        v = latest_verdict
        b_z = v.behavior_sigma
        c_z = v.cost_sigma

        b_bar = render_meter_bar(b_z)
        c_bar = render_meter_bar(c_z)

        b_label = (
            f"+{b_z:.1f}σ" if b_z is not None and b_z >= 0 else f"{b_z:.1f}σ" if b_z else "N/A"
        )
        c_label = (
            f"+{c_z:.1f}σ" if c_z is not None and c_z >= 0 else f"{c_z:.1f}σ" if c_z else "N/A"
        )

        b_note = "normal ±1σ" if v.flag_behavior else "flat"
        c_note = "runaway" if v.runaway else "flat" if (c_z and abs(c_z) < 1.0) else ""

        onset_info = ""
        if v.onset_ts_unix:
            dt_str = datetime.fromtimestamp(v.onset_ts_unix, tz=timezone.utc).strftime("%H:%M:%S")
            sec_str = f"{int(v.seconds_after_deploy)}s" if v.seconds_after_deploy else "0s"
            onset_info = f"onset {dt_str} — {sec_str} after {v.version} deployed"

        caveats_html = (
            f'<div class="card-caveat">⚠ caveats: {", ".join(v.caveats)}</div>' if v.caveats else ""
        )
        falsifier_html = (
            f'<div class="card-falsifier">? {v.falsifier}</div>' if v.falsifier else ""
        )

        # Exemplars (worst + median)
        exemplars_rows = []
        for ex in v.exemplars:
            sig_str = f"+{ex.behavior_sigma:.1f}σ" if ex.behavior_sigma >= 0 else f"{ex.behavior_sigma:.1f}σ"
            kind_tag = f"[{ex.kind:<6}]"
            short_id = ex.trace_id[:8] if ex.trace_id else "00000000"
            exemplars_rows.append(
                f'<div class="exemplar-row"><span class="ex-kind">{kind_tag}</span> '
                f'<span class="ex-id">{short_id}…</span> <span class="ex-sig">{sig_str}</span> '
                f'<span class="ex-text">"{ex.output_excerpt}"</span></div>'
            )
        exemplars_html = "\n".join(exemplars_rows) if exemplars_rows else '<div class="ex-text">No exemplars captured</div>'

        hero_card_html = f"""
        <div class="hero-card" style="border-left: 4px solid {accent_color};">
            <div class="card-header">
                <span class="badge" style="background-color: {accent_color};">{v.state.value.upper()}</span>
                <span class="card-title">{v.service_name} · {v.version}</span>
            </div>
            <div class="card-sub">{v.subject.value} · {v.cause.value}</div>
            
            <div class="meter-group">
                <div class="meter-row">
                    <span class="meter-label">behavior</span>
                    <span class="meter-val">{b_label:>7}</span>
                    <span class="meter-bar">{b_bar}</span>
                    <span class="meter-note">{b_note}</span>
                </div>
                <div class="meter-row">
                    <span class="meter-label">cost</span>
                    <span class="meter-val">{c_label:>7}</span>
                    <span class="meter-bar">{c_bar}</span>
                    <span class="meter-note">{c_note}</span>
                </div>
            </div>

            <div class="card-meta">
                {f'<div>{onset_info}</div>' if onset_info else ''}
                <div>n={v.samples} · baseline {v.baseline_version or 'reference'} (n={v.baseline_samples})</div>
            </div>

            {caveats_html}
            {falsifier_html}

            <div class="evidence-section">
                <div class="evidence-title">evidence</div>
                {exemplars_html}
            </div>
        </div>
        """
    else:
        hero_card_html = f"""
        <div class="hero-card" style="border-left: 4px solid {accent_color};">
            <div class="card-header">
                <span class="badge" style="background-color: {accent_color};">WARMING</span>
                <span class="card-title">Collecting baseline reference</span>
            </div>
            <div class="card-sub">pipeline initializing</div>
        </div>
        """

    # Zone 2: Verdict Feed
    feed_rows = []
    for idx, f_v in enumerate(verdict_feed[:50]):
        dt = datetime.fromtimestamp(f_v.ts_unix, tz=timezone.utc).strftime("%H:%M:%S")
        f_color = STATE_COLORS.get(f_v.state.value, "#6b7280")
        feed_rows.append(
            f"""
            <div class="feed-item" onclick="toggleFeedItem('{idx}')">
                <div class="feed-summary">
                    <span class="feed-time">{dt}</span>
                    <span class="feed-state" style="color: {f_color};">● {f_v.state.value.upper()}</span>
                    <span class="feed-sentence">{f_v.sentence}</span>
                </div>
                <div id="feed-details-{idx}" class="feed-details" style="display: none;">
                    <pre>{json.dumps(f_v.to_dict(), indent=2)}</pre>
                </div>
            </div>
            """
        )
    feed_html = "\n".join(feed_rows) if feed_rows else '<div class="feed-empty">No verdicts recorded yet</div>'

    # Zone 3: Health Strip
    spans_rx = int(health_snapshot.get("spans_received", 0))
    spans_sc = int(health_snapshot.get("spans_scored", 0))
    spans_sk = int(health_snapshot.get("spans_skipped", 0))
    n_scopes = int(health_snapshot.get("scopes", len(scopes)))
    v_emitted = int(health_snapshot.get("verdicts_emitted", 0))
    emit_errs = int(health_snapshot.get("emit_errors", 0))

    import time
    uptime_sec = int(time.time() - start_time)
    uptime_m, uptime_s = divmod(uptime_sec, 60)
    uptime_str = f"{uptime_m}m {uptime_s}s"

    health_strip_html = (
        f"spans: {spans_rx} received / {spans_sc} scored / {spans_sk} skipped · "
        f"scopes: {n_scopes} · verdicts emitted: {v_emitted} · errors: {emit_errs} · "
        f"uptime: {uptime_str} · vitals {__version__} · "
        f'<a href="/docs/blind-spots.md" target="_blank" style="color: #71717a; text-decoration: underline;">blind spots</a>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vitals Console</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: #09090b;
            color: #e4e4e7;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            padding: 24px 16px;
            display: flex;
            justify-content: center;
        }}
        .container {{
            width: 100%;
            max-width: 900px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .hero-card {{
            background-color: #18181b;
            border: 1px solid #27272a;
            border-radius: 8px;
            padding: 20px;
        }}
        .card-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 6px;
        }}
        .badge {{
            color: #09090b;
            font-weight: 700;
            font-size: 12px;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .card-title {{
            font-size: 18px;
            font-weight: 700;
            color: #f4f4f5;
        }}
        .card-sub {{
            color: #a1a1aa;
            font-size: 13px;
            margin-bottom: 16px;
        }}
        .meter-group {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 16px;
            background-color: #09090b;
            padding: 12px;
            border-radius: 6px;
        }}
        .meter-row {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 13px;
        }}
        .meter-label {{ width: 80px; color: #a1a1aa; }}
        .meter-val {{ width: 60px; color: #f4f4f5; font-weight: 600; }}
        .meter-bar {{ color: #22c55e; letter-spacing: 1px; }}
        .meter-note {{ color: #71717a; font-size: 12px; margin-left: 8px; }}
        .card-meta {{ color: #a1a1aa; font-size: 13px; margin-bottom: 12px; display: flex; flex-direction: column; gap: 4px; }}
        .card-caveat {{ color: #f59e0b; font-size: 13px; margin-bottom: 6px; }}
        .card-falsifier {{ color: #3b82f6; font-size: 13px; margin-bottom: 16px; }}
        .evidence-section {{ border-top: 1px solid #27272a; pt: 12px; margin-top: 12px; padding-top: 12px; }}
        .evidence-title {{ color: #a1a1aa; font-size: 12px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }}
        .exemplar-row {{ font-size: 12px; line-height: 1.6; color: #d4d4d8; display: flex; gap: 8px; }}
        .ex-kind {{ color: #a1a1aa; width: 70px; }}
        .ex-id {{ color: #71717a; width: 70px; }}
        .ex-sig {{ color: #f59e0b; width: 50px; font-weight: 600; }}
        .ex-text {{ color: #e4e4e7; flex: 1; word-break: break-word; }}

        .zone-title {{ color: #a1a1aa; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
        .feed-container {{
            background-color: #18181b;
            border: 1px solid #27272a;
            border-radius: 8px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            max-height: 400px;
            overflow-y: auto;
        }}
        .feed-item {{
            padding: 8px 12px;
            border-radius: 4px;
            background-color: #09090b;
            cursor: pointer;
            font-size: 12px;
        }}
        .feed-item:hover {{ background-color: #27272a; }}
        .feed-summary {{ display: flex; gap: 12px; align-items: center; }}
        .feed-time {{ color: #71717a; width: 60px; }}
        .feed-state {{ font-weight: 600; width: 100px; }}
        .feed-sentence {{ color: #d4d4d8; flex: 1; }}
        .feed-details {{ margin-top: 8px; padding: 8px; background-color: #18181b; border-radius: 4px; overflow-x: auto; color: #a1a1aa; }}
        .feed-empty {{ color: #71717a; font-size: 13px; text-align: center; padding: 20px; }}

        .health-strip {{
            background-color: #18181b;
            border: 1px solid #27272a;
            border-radius: 6px;
            padding: 10px 16px;
            font-size: 12px;
            color: #71717a;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container" id="console-root">
        {hero_card_html}
        <div>
            <div class="zone-title">Verdict Feed</div>
            <div class="feed-container">
                {feed_html}
            </div>
        </div>
        <div class="health-strip">
            {health_strip_html}
        </div>
    </div>
    <script>
        function toggleFeedItem(idx) {{
            const el = document.getElementById('feed-details-' + idx);
            if (el) {{
                el.style.display = (el.style.display === 'none') ? 'block' : 'none';
            }}
        }}

        setInterval(async () => {{
            try {{
                const res = await fetch('/');
                if (res.ok) {{
                    const text = await res.text();
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(text, 'text/html');
                    const newRoot = doc.getElementById('console-root');
                    if (newRoot) {{
                        document.getElementById('console-root').innerHTML = newRoot.innerHTML;
                    }}
                }}
            }} catch (e) {{
                console.error('Auto-refresh poll error:', e);
            }}
        }}, 2000);
    </script>
</body>
</html>
"""
