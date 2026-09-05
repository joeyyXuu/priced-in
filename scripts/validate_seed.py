"""Offline seed integrity checks; no financial metrics or source certification."""

import csv
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import sys
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
BOOL = {"TRUE", "FALSE"}
EVENT_FIELDS = {
    "candidate_id", "ticker", "approx_period", "event_date", "release_timing",
    "event_type", "fiscal_quarter", "expected_pattern", "why_selected",
    "recall_confidence", "source_url", "verified", "headline", "release_time_et",
    "timing_source_url", "timing_notes", "sample_role", "analysis_scope",
}
ESTIMATE_FIELDS = {
    "candidate_id", "fiscal_quarter", "actual_eps", "consensus_eps",
    "actual_eps_basis", "consensus_eps_basis", "currency", "share_unit",
    "split_basis", "consensus_snapshot_date", "snapshot_kind", "actual_source_url",
    "consensus_source_url", "comparison_source_url", "comparability_verified", "notes",
    "basis_review_source_url",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_csv(name, required):
    with (ROOT / "data" / name).open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames or []
        require(len(columns) == len(set(columns)), f"{name}: duplicate columns")
        require(required <= set(columns), f"{name}: missing required columns")
        rows = list(reader)
    require(rows, f"{name}: empty file")
    require(all(None not in r and None not in r.values() for r in rows),
            f"{name}: malformed CSV row")
    return rows


def keyed(rows, label):
    ids = [r["candidate_id"] for r in rows]
    require(len(ids) == len(set(ids)), f"{label}: duplicate candidate_id")
    require(all(re.fullmatch(r"C\d{2,}", cid) for cid in ids),
            f"{label}: invalid candidate_id")
    return dict(zip(ids, rows))


def url(value):
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate(events, candidates, reviews, estimates):
    event_map = keyed(events, "events")
    candidate_map = keyed(candidates, "candidates")
    review_map = keyed(reviews, "review")
    estimate_map = keyed(estimates, "estimates")
    require({f"C{i:02}" for i in range(1, 27)} <= candidate_map.keys(),
            "Original 26 research candidates must be retained")
    require(review_map.keys() == candidate_map.keys(), "Review coverage differs from research")
    require(event_map.keys() <= candidate_map.keys(), "Production contains unknown candidates")
    require(all(r["included"] in BOOL for r in reviews), "Invalid inclusion flag")
    require({r["candidate_id"] for r in reviews if r["included"] == "TRUE"}
            == event_map.keys(), "Review inclusion disagrees with production")
    require(len(events) == 20, "Current reviewed selection must contain 20 events")
    require(len({r["ticker"] for r in events}) <= 7, "More than seven tickers")
    years = set()
    for r in events:
        cid = r["candidate_id"]
        day = date.fromisoformat(r["event_date"])
        years.add(day.year)
        require(r["approx_period"] == r["event_date"][:7], f"{cid}: approximate month mismatch")
        require(r["ticker"] in {"NVDA", "AMD", "INTC", "TSM", "MU", "AVGO", "SOXX"},
                f"{cid}: unexpected ticker")
        require(r["release_timing"] in {"bmo", "amc", "intraday"}, f"{cid}: invalid timing")
        require(r["event_type"] in {"earnings", "guidance", "macro", "product", "acquisition"},
                f"{cid}: invalid event type")
        require(r["expected_pattern"] in {"aligned", "divergent", "macro"},
                f"{cid}: invalid hypothesis")
        require(r["verified"] in BOOL, f"{cid}: invalid verified flag")
        require(r["verified"] == "TRUE", f"{cid}: unverified production event metadata")
        for field in ("headline", "why_selected", "timing_notes", "sample_role"):
            require(bool(r[field].strip()), f"{cid}: blank {field}")
        require(len(r["headline"]) <= 120, f"{cid}: headline exceeds 120 characters")
        require(r["headline"] != r["why_selected"], f"{cid}: headline repeats interpretation")
        require(url(r["source_url"]) and url(r["timing_source_url"]), f"{cid}: missing source URL")
        if r["release_time_et"]:
            require(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", r["release_time_et"]),
                    f"{cid}: invalid release time")
            minute = r["release_time_et"]
            category = "bmo" if minute < "09:30" else "intraday" if minute < "16:00" else "amc"
            require(category == r["release_timing"], f"{cid}: time/category mismatch")
        if r["event_type"] in {"macro", "acquisition"}:
            require(not r["fiscal_quarter"], f"{cid}: inapplicable fiscal quarter")
        else:
            require(re.fullmatch(r"FY\d{2}Q[1-4]", r["fiscal_quarter"]),
                    f"{cid}: invalid fiscal quarter")
        role = r["sample_role"]
        require(r["analysis_scope"] in {"eps_and_price", "qualitative", "macro_price"},
                f"{cid}: invalid analysis scope")
        require(role in {"divergence_candidate", "comparison", "additional_aligned", "qualitative", "macro"},
                f"{cid}: invalid sample role")
        if role in {"divergence_candidate", "comparison", "additional_aligned"}:
            require(r["event_type"] == "earnings", f"{cid}: non-earnings in EPS role")
            require(r["analysis_scope"] == "eps_and_price", f"{cid}: EPS role outside EPS scope")
            expected = "divergent" if role == "divergence_candidate" else "aligned"
            require(r["expected_pattern"] == expected, f"{cid}: role/hypothesis mismatch")
        if r["event_type"] == "macro":
            require(role == "macro" and r["expected_pattern"] == "macro", f"{cid}: invalid macro role")
            require(r["analysis_scope"] == "macro_price", f"{cid}: invalid macro scope")
        if r["event_type"] == "guidance":
            require(role == "qualitative", f"{cid}: guidance lacks quantitative expectation")
        if role == "qualitative":
            require(r["analysis_scope"] == "qualitative", f"{cid}: qualitative role in automatic scope")
        if r["analysis_scope"] == "eps_and_price":
            require(r["event_type"] == "earnings", f"{cid}: automatic EPS scope requires earnings")
        for field in ("event_type", "fiscal_quarter", "release_timing", "expected_pattern", "source_url"):
            require(r[field] == review_map[cid]["reviewed_" + field], f"{cid}: review mismatch for {field}")
        require(r["headline"] == review_map[cid]["headline"], f"{cid}: review headline mismatch")
    require(years == set(range(2019, 2026)), "Sample must cover 2019–2025")
    roles = Counter(r["sample_role"] for r in events)
    require(3 <= roles["macro"] <= 4, "Need three or four macro cases")
    require(roles["comparison"] >= 3, "Need three designated comparisons")
    require(roles["divergence_candidate"] >= 8, "Need eight divergence hypotheses (not results)")
    earnings = {r["candidate_id"] for r in events if r["event_type"] == "earnings"}
    require(estimate_map.keys() == earnings, "EPS inputs must cover precisely selected earnings")
    eligible, blocked = [], []
    for cid, r in estimate_map.items():
        require(r["fiscal_quarter"] == event_map[cid]["fiscal_quarter"], f"{cid}: EPS quarter mismatch")
        for field in ("actual_eps", "consensus_eps"):
            try:
                number = Decimal(r[field])
            except InvalidOperation as error:
                raise ValueError(f"{cid}: invalid {field}") from error
            require(number.is_finite(), f"{cid}: non-finite {field}")
        snapshot = date.fromisoformat(r["consensus_snapshot_date"])
        event_day = date.fromisoformat(event_map[cid]["event_date"])
        require(snapshot <= event_day, f"{cid}: snapshot after event")
        require(r["snapshot_kind"] in {"pre_release_publication", "reported_at_release"},
                f"{cid}: unknown snapshot provenance")
        if r["snapshot_kind"] == "reported_at_release":
            require(snapshot == event_day, f"{cid}: release-day proxy date mismatch")
        for field in ("actual_source_url", "consensus_source_url", "comparison_source_url", "basis_review_source_url"):
            require(url(r[field]), f"{cid}: invalid {field}")
        require(r["comparability_verified"] in BOOL, f"{cid}: invalid comparability flag")
        require(r["actual_eps_basis"] in {"gaap", "non_gaap", "ifrs"}, f"{cid}: unknown actual basis")
        require(r["consensus_eps_basis"] in {"gaap", "non_gaap", "ifrs", "unverified"},
                f"{cid}: unknown consensus basis")
        require(r["currency"] == "USD" and r["split_basis"] == "as_reported_at_event",
                f"{cid}: unexpected currency/split units")
        expected_unit = "adr" if event_map[cid]["ticker"] == "TSM" else "diluted_common_share"
        require(r["share_unit"] == expected_unit, f"{cid}: incorrect share unit")
        require(bool(r["notes"].strip()), f"{cid}: missing EPS provenance notes")
        if r["comparability_verified"] == "TRUE":
            require(r["actual_eps_basis"] == r["consensus_eps_basis"], f"{cid}: incompatible EPS bases")
            eligible.append(cid)
        else:
            blocked.append(cid)
            require(event_map[cid]["analysis_scope"] == "qualitative",
                    f"{cid}: unverified EPS pair must remain qualitative-only")
    return roles, sorted(eligible), sorted(blocked)


def validate_p1(events, estimates, evidence):
    """Check manual evidence coverage; percentages are transcribed, never calculated here."""
    event_map = keyed(events, "events")
    estimate_map = keyed(estimates, "estimates")
    evidence_map = keyed(evidence, "P1 evidence")
    required_ids = {r["candidate_id"] for r in events if r["analysis_scope"] == "eps_and_price"}
    require(evidence_map.keys() == required_ids, "P1 evidence must cover exactly the automatic EPS sample")
    counts = Counter()
    for cid, r in evidence_map.items():
        event, estimate = event_map[cid], estimate_map[cid]
        require(estimate["comparability_verified"] == "TRUE", f"{cid}: P1 case has unverified EPS")
        require(r["verified"] == "TRUE", f"{cid}: unverified P1 evidence")
        require(r["window"] == "one_day_close_to_close", f"{cid}: wrong reaction window")
        reaction_day = date.fromisoformat(r["reaction_date"])
        announcement_day = date.fromisoformat(event["event_date"])
        require(reaction_day.weekday() < 5, f"{cid}: reaction on weekend")
        require(reaction_day > announcement_day if event["release_timing"] == "amc"
                else reaction_day >= announcement_day, f"{cid}: reaction precedes announcement availability")
        require(date.fromisoformat(r["reviewed_on"]) >= reaction_day, f"{cid}: invalid review date")
        require(r["eps_result"] in {"beat", "miss", "meet"}, f"{cid}: invalid EPS direction")
        actual, consensus = Decimal(estimate["actual_eps"]), Decimal(estimate["consensus_eps"])
        expected = "beat" if actual > consensus else "miss" if actual < consensus else "meet"
        require(r["eps_result"] == expected, f"{cid}: EPS direction contradicts sourced inputs")
        require(r["price_direction"] in {"up", "down", "flat"}, f"{cid}: invalid price direction")
        observed = (r["eps_result"], r["price_direction"])
        expected_pattern = "divergent" if observed in {("beat", "down"), ("miss", "up")} else "aligned" if observed in {("beat", "up"), ("miss", "down")} else "neutral"
        require(r["reviewed_pattern"] == expected_pattern, f"{cid}: inconsistent reviewed pattern")
        require(expected_pattern == event["expected_pattern"], f"{cid}: hypothesis needs review")
        try:
            reported = Decimal(r["reported_return_pct"])
        except InvalidOperation as error:
            raise ValueError(f"{cid}: invalid transcribed return") from error
        require(reported.is_finite(), f"{cid}: non-finite transcribed return")
        require((reported > 0 and r["price_direction"] == "up")
                or (reported < 0 and r["price_direction"] == "down")
                or (reported == 0 and r["price_direction"] == "flat"), f"{cid}: source return sign mismatch")
        require(url(r["source_url"]) and url(r["corroborating_source_url"]), f"{cid}: missing P1 sources")
        require(r["evidence_kind"] in {"market_brief", "closing_news", "retrospective_session_report", "historical_price_table"},
                f"{cid}: unsupported evidence kind")
        require(bool(r["notes"].strip()), f"{cid}: missing evidence context")
        if event["sample_role"] == "comparison":
            require(expected_pattern == "aligned", f"{cid}: comparison not aligned")
            counts["comparison"] += 1
        if event["sample_role"] == "divergence_candidate":
            require(expected_pattern == "divergent", f"{cid}: divergence case not supported")
            counts["divergent"] += 1
    require(counts["divergent"] >= 8 and counts["comparison"] >= 3,
            "P1 requires eight supported sign-divergence cases and three supported aligned comparisons")
    return counts


def main():
    events = load_csv("events.csv", EVENT_FIELDS)
    candidates = load_csv("events_candidates.csv", {"candidate_id", "why_selected"})
    reviews = load_csv("event_review.csv", {
        "candidate_id", "included", "headline", "reviewed_event_type", "reviewed_fiscal_quarter",
        "reviewed_release_timing", "reviewed_expected_pattern", "reviewed_source_url",
        "field_corrections", "review_notes",
    })
    estimates = load_csv("estimates.csv", ESTIMATE_FIELDS)
    roles, eligible, blocked = validate(events, candidates, reviews, estimates)
    evidence = load_csv("p1_validation.csv", {
        "candidate_id", "reaction_date", "window", "eps_result", "price_direction",
        "reviewed_pattern", "reported_return_pct", "evidence_kind", "source_url",
        "corroborating_source_url", "reviewed_on", "verified", "notes",
    })
    counts = validate_p1(events, estimates, evidence)
    print(f"PASS: {len(candidates)} research records, {len(events)} selected events, {len(estimates)} EPS pairs.")
    print(f"Roles: {roles['divergence_candidate']} divergence hypotheses, {roles['comparison']} comparisons, {roles['macro']} macro events.")
    print(f"Comparable EPS inputs: {len(eligible)}. Blocked EPS inputs: {', '.join(blocked) or 'none'}.")
    print(f"P1 evidence coverage: {counts['divergent']} sign-divergence cases, {counts['comparison']} aligned comparisons.")
    print("P1 seed checks passed with TSM restricted to qualitative analysis. Published return observations are not SQL metrics or causal findings.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, csv.Error) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
