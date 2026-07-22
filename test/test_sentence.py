"""Contract test — Verdict.sentence snapshot for each of the five §7 examples."""

from vitals.verdict.types import (
    Cause,
    InconclusiveReason,
    Subject,
    Verdict,
    VerdictState,
)


def test_sentence_steady():
    v = Verdict(
        verdict_id="1234567890abcdef",
        ts_unix=1700000000.0,
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        version="v1",
        baseline_version=None,
        state=VerdictState.STEADY,
        subject=Subject.TIME,
        cause=Cause.NONE,
        flag_cost=False,
        flag_behavior=False,
        runaway=False,
        behavior_sigma=0.3,
        cost_sigma=0.1,
        cost_usd_per_req=0.001,
        baseline_cost_usd_per_req=0.001,
        velocity_ratio=1.0,
        samples=412,
        baseline_samples=30,
        onset_ts_unix=None,
        seconds_after_deploy=None,
        inconclusive_reason=None,
        caveats=(),
        falsifier="would flip to CHANGED at behavior >=3σ (currently 0.3σ)",
        warming_progress=None,
        exemplars=(),
    )
    assert v.sentence == "STEADY · ragapp v1 · behavior +0.3σ · cost +0.1σ · n=412"


def test_sentence_changed_behavior():
    v = Verdict(
        verdict_id="1234567890abcdef",
        ts_unix=1774276327.0,
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        version="v2",
        baseline_version="v1",
        state=VerdictState.CHANGED,
        subject=Subject.RELEASE,
        cause=Cause.RELEASE,
        flag_cost=False,
        flag_behavior=True,
        runaway=False,
        behavior_sigma=4.2,
        cost_sigma=0.3,
        cost_usd_per_req=0.001,
        baseline_cost_usd_per_req=0.001,
        velocity_ratio=1.0,
        samples=1240,
        baseline_samples=30,
        onset_ts_unix=1774276327.0,  # 14:32:07 UTC
        seconds_after_deploy=90.0,
        inconclusive_reason=None,
        caveats=("output_length_-31%",),
        falsifier="would flip to STEADY if input drift >=3σ (currently 0.4σ)",
        warming_progress=None,
        exemplars=(),
    )
    assert (
        v.sentence
        == "CHANGED · behavior · v2 vs v1 · +4.2σ (normal ±1σ) · cost flat +0.3σ · onset 14:32:07, 90s after v2 deployed · n=1240"
    )


def test_sentence_changed_cost_runaway():
    v = Verdict(
        verdict_id="1234567890abcdef",
        ts_unix=1700000000.0,
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        version="v1",
        baseline_version=None,
        state=VerdictState.CHANGED,
        subject=Subject.TIME,
        cause=Cause.UNATTRIBUTED,
        flag_cost=True,
        flag_behavior=False,
        runaway=True,
        behavior_sigma=0.4,
        cost_sigma=15.0,
        cost_usd_per_req=0.05,
        baseline_cost_usd_per_req=0.001,
        velocity_ratio=51.0,
        samples=88,
        baseline_samples=30,
        onset_ts_unix=None,
        seconds_after_deploy=None,
        inconclusive_reason=None,
        caveats=(),
        falsifier="would flip to STEADY if velocity returns within 3σ for 120s",
        warming_progress=None,
        exemplars=(),
    )
    assert (
        v.sentence
        == "CHANGED · cost · runaway: 51× baseline burn rate · behavior flat +0.4σ · cause unattributed — no release in the last 5m · n=88"
    )


def test_sentence_inconclusive_input_shift():
    v = Verdict(
        verdict_id="1234567890abcdef",
        ts_unix=1700000000.0,
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        version="v1",
        baseline_version=None,
        state=VerdictState.INCONCLUSIVE,
        subject=Subject.TIME,
        cause=Cause.NONE,
        flag_cost=False,
        flag_behavior=False,
        runaway=False,
        behavior_sigma=3.8,
        cost_sigma=0.2,
        cost_usd_per_req=0.001,
        baseline_cost_usd_per_req=0.001,
        velocity_ratio=1.0,
        samples=205,
        baseline_samples=30,
        onset_ts_unix=None,
        seconds_after_deploy=None,
        inconclusive_reason=InconclusiveReason.INPUT_SHIFT,
        caveats=(),
        falsifier="would resolve if input drift drops below 3σ",
        warming_progress=None,
        exemplars=(),
        input_sigma=4.1,
    )
    assert (
        v.sentence
        == "INCONCLUSIVE · input_shift · behavior +3.8σ but input +4.1σ — your traffic changed, not your model · n=205"
    )


def test_sentence_warming():
    v = Verdict(
        verdict_id="1234567890abcdef",
        ts_unix=1700000000.0,
        service_name="ragapp",
        gen_ai_system="openai",
        model="gpt-4o",
        version="v1",
        baseline_version=None,
        state=VerdictState.WARMING,
        subject=Subject.TIME,
        cause=Cause.NONE,
        flag_cost=False,
        flag_behavior=False,
        runaway=False,
        behavior_sigma=None,
        cost_sigma=None,
        cost_usd_per_req=None,
        baseline_cost_usd_per_req=None,
        velocity_ratio=None,
        samples=340,
        baseline_samples=30,
        onset_ts_unix=None,
        seconds_after_deploy=None,
        inconclusive_reason=InconclusiveReason.WARMING,
        caveats=(),
        falsifier="",
        warming_progress=(340, 1000),
        exemplars=(),
    )
    assert v.sentence == "WARMING · ragapp v1 · collecting reference 340/1000 · est. 22m"
