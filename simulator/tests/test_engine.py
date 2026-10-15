import json

import pytest

from agentpause import AgentPause, DecisionType, ResponseType
from agentpause_sim import (
    ConditionSpec,
    EngineError,
    EpisodeEngine,
    HumanResponse,
    PolicySpec,
    SimulatedUser,
    load_scenario,
    run_episode,
    summarize,
)

POLICIES = [
    "full_autonomy",
    "always_confirm",
    "fixed_threshold",
    "rule_based",
    "confidence_threshold",
    "myopic_voi",
    "adaptive",
    "user_customized",
    "learned",
]


def engine(sid="travel", policy="adaptive", seed=7, episode=0, user=True):
    return EpisodeEngine(
        load_scenario(sid),
        AgentPause(policy, explain="none"),
        seed=seed,
        episode=episode,
        user=SimulatedUser() if user else None,
    )


@pytest.mark.parametrize("policy", POLICIES)
@pytest.mark.parametrize("sid", ["travel", "email", "shopping", "files", "calendar", "research"])
def test_every_policy_completes_every_scenario(policy, sid):
    eng = run_episode(sid, PolicySpec(policy), ConditionSpec(), seed=11, episode=2)
    assert eng.done
    assert eng.state.records
    s = summarize(eng.state, len(eng.scenario.steps))
    assert s.necessary + s.unnecessary == s.interventions
    assert s.errors_caught + s.errors_harmful <= s.errors_total


def test_episodes_are_deterministic():
    a = run_episode("email", PolicySpec("adaptive"), ConditionSpec(), seed=3, episode=5)
    b = run_episode("email", PolicySpec("adaptive"), ConditionSpec(), seed=3, episode=5)
    strip = lambda recs: [{k: v for k, v in r.items() if k != "decision_latency_ms"} for r in recs]  # noqa: E731
    assert strip(a.state.records) == strip(b.state.records)
    assert a.state.errors.keys() == b.state.errors.keys()
    assert a.outcome() == b.outcome()


def test_common_random_numbers_across_policies():
    """Every policy faces the same injected errors and the same true intent for a seed/episode."""
    states = [engine(policy=p, seed=5, episode=9).state for p in POLICIES]
    assert len({tuple(sorted(s.errors)) for s in states}) == 1
    assert len({tuple(sorted(s.truth.items())) for s in states}) == 1


def test_different_episodes_differ():
    injected = {tuple(sorted(engine(episode=e).state.errors)) for e in range(40)}
    assert len(injected) > 3


def test_full_autonomy_never_interrupts_and_misses_everything():
    for episode in range(30):
        eng = run_episode("files", PolicySpec("full_autonomy"), ConditionSpec(), seed=1, episode=episode)
        s = summarize(eng.state, len(eng.scenario.steps))
        assert s.interventions == 0
        assert s.missed_interventions == s.errors_harmful


def test_shopping_payment_verification_always_needs_the_human():
    eng = run_episode("shopping", PolicySpec("full_autonomy"), ConditionSpec(), seed=1, episode=0)
    blocks = [r for r in eng.state.records if r["decision"] == "BLOCK"]
    assert [r["step_id"] for r in blocks] == ["verify_payment"]
    assert blocks[0]["necessary"] is True


def _find_episode_with(error_id, sid="email", policy="always_confirm", seed=1):
    for episode in range(300):
        eng = EpisodeEngine(load_scenario(sid), AgentPause(policy, explain="none"), seed=seed, episode=episode)
        if error_id in eng.state.errors:
            return eng
    raise AssertionError(f"no episode with {error_id}")


def drive_to_card(eng):
    while eng.state.status == "running":
        result = eng.step()
        if result.card:
            return result.card
    return None


def test_approving_a_visible_mistake_causes_harm_and_counts_as_human_miss():
    eng = _find_episode_with("mistake:autocomplete_recipient")
    while True:
        card = drive_to_card(eng)
        assert card is not None
        if card["step_id"] == "send_email":
            break
        eng.respond(HumanResponse(ResponseType.APPROVE))
    assert "j.smith@gmail.com" in card["action"]["preview"]["To"], "the mistake is visible in the preview"
    assert "shown_errors" not in eng.public_pending(), "ground truth is hidden from participants"
    eng.respond(HumanResponse(ResponseType.APPROVE))
    error = eng.state.errors["mistake:autocomplete_recipient"]
    assert error.status == "harm" and error.shown_at
    while not eng.done:
        if eng.state.status == "awaiting_human":
            eng.respond(HumanResponse(ResponseType.APPROVE))
        else:
            eng.step()
    s = summarize(eng.state, len(eng.scenario.steps))
    assert s.human_miss_errors >= 1 and s.missed_interventions == 0


def test_editing_fixes_the_mistake():
    eng = _find_episode_with("mistake:autocomplete_recipient")
    while True:
        card = drive_to_card(eng)
        if card["step_id"] == "send_email":
            break
        eng.respond(HumanResponse(ResponseType.APPROVE))
    eng.respond(HumanResponse(ResponseType.EDIT))
    assert eng.state.errors["mistake:autocomplete_recipient"].status == "caught"


def test_reject_reproposes_then_takes_over():
    eng = engine("email", "always_confirm", user=False)
    card = drive_to_card(eng)
    step = card["step_index"]
    for _ in range(3):
        eng.respond(HumanResponse(ResponseType.REJECT))
        if eng.state.index != step:
            break
        card = drive_to_card(eng)
        assert card["step_index"] == step
    assert eng.state.index == step + 1, "after max_attempts rejections the user takes over"


def test_ask_why_keeps_the_card_open_and_cancel_ends_the_task():
    eng = engine("email", "always_confirm", user=False)
    drive_to_card(eng)
    result = eng.respond(HumanResponse(ResponseType.ASK_WHY))
    assert eng.state.status == "awaiting_human" and result.events[0]["type"] == "ask_why"
    eng.respond(HumanResponse(ResponseType.CANCEL_TASK))
    assert eng.state.status == "cancelled"
    assert all(e.status in ("averted", "caught") for e in eng.state.errors.values())


def test_respond_without_card_and_step_when_done_raise():
    eng = engine(user=False)
    with pytest.raises(EngineError):
        eng.respond(HumanResponse(ResponseType.APPROVE))
    with pytest.raises(EngineError):
        engine(user=False).run()


def test_clarification_answer_resolves_assumption_and_rework():
    for episode in range(200):
        eng = EpisodeEngine(load_scenario("travel"), AgentPause("myopic_voi", explain="none"), seed=2, episode=episode)
        if "assumption:travel_date" in eng.state.errors:
            break
    card = drive_to_card(eng)
    assert card["decision"]["decision"] == DecisionType.CLARIFY.value
    assert "travel_date" in card["assumption_ids"]
    truth = eng.state.truth["travel_date"]
    eng.respond(HumanResponse(ResponseType.ANSWER, answers={"travel_date": truth}))
    assert eng.state.values["travel_date"] == truth
    assert eng.state.errors["assumption:travel_date"].status == "caught"


def test_skip_if_skips_unwanted_steps():
    for episode in range(300):
        eng = EpisodeEngine(
            load_scenario("travel"), AgentPause("full_autonomy", explain="none"), seed=4, episode=episode
        )
        if eng.state.truth["share_itinerary"] == "Do not email anyone":
            break
    eng.state.values["share_itinerary"] = "Do not email anyone"
    eng.user = SimulatedUser()
    eng.run()
    assert any(e.get("skipped") for e in eng.state.executed)
    assert all(r["step_id"] != "send_itinerary" for r in eng.state.records)


def test_resume_from_json_matches_uninterrupted_run():
    def play(eng, resume_after=None):
        n = 0
        while not eng.done:
            if eng.state.status == "awaiting_human":
                eng.respond(HumanResponse(ResponseType.APPROVE, response_time_s=3.0))
            else:
                eng.step()
            n += 1
            if resume_after is not None and n == resume_after:
                data = json.loads(json.dumps(eng.to_dict()))
                eng = EpisodeEngine.from_dict(data, load_scenario(data["scenario_id"]))
        return eng

    a = play(engine("calendar", user=False, episode=4))
    b = play(engine("calendar", user=False, episode=4), resume_after=3)
    strip = lambda recs: [{k: v for k, v in r.items() if k != "decision_latency_ms"} for r in recs]  # noqa: E731
    assert strip(a.state.records) == strip(b.state.records)
    assert a.outcome() == b.outcome()


def test_brief_uses_true_intent_and_preview_uses_agent_values():
    eng = engine(user=False)
    brief = eng.brief()
    for _a_id, truth in eng.state.truth.items():
        assert truth in brief
    ctx = eng.build_context()
    assert ctx.metadata["simulated"] is True
    assert ctx.provenance["cognitive_load"].value == "simulated"
