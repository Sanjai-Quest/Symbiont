
import sys
from pathlib import Path
from collections import defaultdict, Counter

import numpy as np

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent),
)

import phase1_baseline_control as baseline


FS = 200
FOLLOWUP_SECONDS = 60
FOLLOWUP_SAMPLES = FS * FOLLOWUP_SECONDS


def main():

    record = baseline.load_signal()

    arousals, stages = baseline.load_labels_and_stages(
        record.sig_len
    )

    events = baseline.parse_events()

    print(f"Record: {baseline.RECORD_ID}")
    print(f"Signal length: {record.sig_len:,}")
    print(f"Label length: {len(arousals):,}")
    print(f"Parsed events: {len(events)}")
    print(f"Event types: {dict(Counter(item['type'] for item in events))}")

    # Store all annotated event intervals for overlap detection.
    event_intervals = [
        (item["start"], item["end"], item["type"])
        for item in events
    ]

    results = []

    print("\nPOST-EVENT OBSERVABILITY AUDIT")
    print("=" * 120)

    # ---------------------------------------------------------
    # EVENT-LEVEL OBSERVABILITY ANALYSIS
    # ---------------------------------------------------------

    for event in events:

        end = event["end"]

        limit = min(
            end + FOLLOWUP_SAMPLES,
            len(arousals),
        )

        followup = arousals[end:limit]

        recording_truncated = (
            limit - end < FOLLOWUP_SAMPLES
        )

        # Find the first scored sample.
        scored_indices = np.flatnonzero(
            followup != -1
        )

        first_scored = (
            int(scored_indices[0])
            if len(scored_indices)
            else None
        )

        # -----------------------------------------------------
        # CASE 1: No scorable follow-up
        # -----------------------------------------------------

        if first_scored is None:

            if recording_truncated:
                censor_reason = "RECORDING_END"
            else:
                censor_reason = "NO_SCORABLE_FOLLOWUP"

            results.append({
                **event,
                "scorable_delay": None,
                "continuous_observation": 0.0,
                "arousal_latency": None,
                "censor_reason": censor_reason,
                "left_censored_arousal": False,
                "first_scored_label": None,
                "other_events_in_followup": [],
                "overlap_contaminated": False,
            })

            continue

        # -----------------------------------------------------
        # CASE 2: Scorable follow-up exists
        # -----------------------------------------------------

        observation_start = end + first_scored

        remaining = arousals[
            observation_start:limit
        ]

        excluded = np.flatnonzero(
            remaining == -1
        )

        continuous_samples = (
            int(excluded[0])
            if len(excluded)
            else len(remaining)
        )

        # Determine censoring reason.
        if len(excluded):
            censor_reason = "LABEL_CENSORED"

        elif recording_truncated:
            censor_reason = "RECORDING_END"

        else:
            censor_reason = "FULL_FOLLOWUP"

        # -----------------------------------------------------
        # Detect confirmed 0 -> +1 arousal transitions.
        # -----------------------------------------------------

        arousal_onsets = np.flatnonzero(
            (remaining == 1)
            & np.r_[False, remaining[:-1] == 0]
        )

        valid_arousals = arousal_onsets[
            arousal_onsets < continuous_samples
        ]

        # Latency is measured from the original event end.
        latency = (
            float(
                (first_scored + valid_arousals[0]) / FS
            )
            if len(valid_arousals)
            else None
        )

        # Observation begins during an existing arousal.
        left_censored_arousal = bool(
            len(remaining) > 0
            and remaining[0] == 1
        )

        first_scored_label = int(
            followup[first_scored]
        )

        # -----------------------------------------------------
        # Detect other annotated events in follow-up.
        # -----------------------------------------------------

        
        # -----------------------------------------------------
        # Classify other annotated events in follow-up.
        # -----------------------------------------------------

        observable_end = observation_start + continuous_samples

        first_arousal_sample = (
            observation_start + int(valid_arousals[0])
            if len(valid_arousals)
            else None
        )

        other_events = []

        for other_start, other_end, other_type in event_intervals:

            # Exclude the current event itself.
            if (
                other_start == event["start"]
                and other_end == event["end"]
                and other_type == event["type"]
            ):
                continue

            # Ignore events outside the observable interval.
            if other_end <= end or other_start >= observable_end:
                continue

            # Event was already underway when the target event ended.
            if other_start < end:
                relation = "PRE_EXISTING_OVERLAP"

            # Another event occurred before the first confirmed arousal.
            elif (
                first_arousal_sample is not None
                and other_start < first_arousal_sample
            ):
                relation = "PRE_AROUSAL_COMPETING_EVENT"

            # Another event started after the confirmed arousal.
            elif (
                first_arousal_sample is not None
                and other_start >= first_arousal_sample
            ):
                relation = "POST_AROUSAL_EVENT"

            else:
                relation = "COMPETING_EVENT_NO_AROUSAL"

            other_events.append({
                "start": other_start,
                "end": other_end,
                "type": other_type,
                "relation": relation,
            })

        overlap_contaminated = any(
            item["relation"] in {
                "PRE_EXISTING_OVERLAP",
                "PRE_AROUSAL_COMPETING_EVENT",
                "COMPETING_EVENT_NO_AROUSAL",
            }
            for item in other_events
        )

        results.append({
            **event,
            "scorable_delay": int(first_scored),
            "continuous_observation": continuous_samples / FS,
            "arousal_latency": latency,
            "censor_reason": censor_reason,
            "left_censored_arousal": left_censored_arousal,
            "first_scored_label": first_scored_label,
            "other_events_in_followup": other_events,
            "overlap_contaminated": overlap_contaminated,
        })

    # ---------------------------------------------------------
    # SUMMARY BY EVENT TYPE
    # ---------------------------------------------------------

    event_types = sorted({
        item["type"] for item in results
    })

    print(
        f"{'TYPE':<25}"
        f"{'N':>5}"
        f"{'SCORABLE':>10}"
        f"{'MEDIAN OBS':>13}"
        f"{'AROUSAL':>10}"
        f"{'LEFT CENS.':>12}"
        f"{'LABEL CENS.':>13}"
        f"{'RECORD END':>12}"
        f"{'OVERLAP':>10}"
    )

    print("-" * 120)

    for event_type in event_types:

        group = [
            item for item in results
            if item["type"] == event_type
        ]

        scorable = [
            item for item in group
            if item["scorable_delay"] is not None
        ]

        observations = [
            item["continuous_observation"]
            for item in scorable
        ]

        arousal_count = sum(
            item["arousal_latency"] is not None
            for item in group
        )

        left_censored_count = sum(
            item["left_censored_arousal"]
            for item in group
        )

        label_censored_count = sum(
            item["censor_reason"] == "LABEL_CENSORED"
            for item in group
        )

        recording_end_count = sum(
            item["censor_reason"] == "RECORDING_END"
            for item in group
        )

        relation_counts = Counter(
            event["relation"]
            for item in group
            for event in item["other_events_in_followup"]
        )

        print(
            event_type,
            "total:", len(group),
            "relations:", dict(relation_counts),
        )

        median_observation = (
            float(np.median(observations))
            if observations else 0.0
        )

        print(
            f"{event_type:<25}"
            f"{len(group):>5}"
            f"{len(scorable):>10}"
            f"{median_observation:>13.2f}"
            f"{arousal_count:>10}"
            f"{left_censored_count:>12}"
            f"{label_censored_count:>13}"
            f"{recording_end_count:>12}"
            f"{sum(item['overlap_contaminated'] for item in group):>10}"
        )

    # ---------------------------------------------------------
    # FIRST SCORABLE LABEL DISTRIBUTION
    # ---------------------------------------------------------

    label_distribution = defaultdict(Counter)

    for result in results:

        label_distribution[result["type"]][
            result["first_scored_label"]
        ] += 1

    print("\nFIRST SCORABLE LABEL DISTRIBUTION")
    print("-" * 65)

    for event_type, counts in sorted(
        label_distribution.items()
    ):

        print(
            event_type,
            dict(counts),
        )

    # ---------------------------------------------------------
    # CENSORING REASON DISTRIBUTION
    # ---------------------------------------------------------

    print("\nCENSORING REASON DISTRIBUTION")
    print("-" * 65)

    censor_distribution = defaultdict(Counter)

    for result in results:

        censor_distribution[result["type"]][
            result["censor_reason"]
        ] += 1

    for event_type, counts in sorted(
        censor_distribution.items()
    ):

        print(
            event_type,
            dict(counts),
        )

    # ---------------------------------------------------------
    # EVENT OVERLAP SUMMARY
    # ---------------------------------------------------------

    print("\nEVENT OVERLAP SUMMARY")
    print("-" * 65)

    for event_type in event_types:

        group = [
            item for item in results
            if item["type"] == event_type
        ]

        contaminated = [
            item for item in group
            if item["overlap_contaminated"]
        ]

        print(
            event_type,
            "total:", len(group),
            "contaminated:", len(contaminated),
            "uncontaminated:",
            len(group) - len(contaminated),
        )

    # ---------------------------------------------------------
    # INDIVIDUAL EVENT DETAILS
    # ---------------------------------------------------------

    print("\nINDIVIDUAL EVENT DETAILS")
    print("-" * 120)

    for item in results:

        print(
            item["type"],
            "start:", item["start"],
            "end:", item["end"],
            "scorable delay:", item["scorable_delay"],
            "first label:", item["first_scored_label"],
            "observation:",
            item["continuous_observation"],
            "arousal latency:", item["arousal_latency"],
            "left censored:",
            item["left_censored_arousal"],
            "censor reason:",
            item["censor_reason"],
            "overlap:", item["overlap_contaminated"],
            "other events:", item["other_events_in_followup"],
        )


if __name__ == "__main__":
    main()
