
"""
SYMBIONT - PHASE 1
Baseline vs Control Analysis

Purpose:
    Compare post-event arousal frequency against matched
    non-event control windows.

Dataset:
    PhysioNet/CinC Challenge 2018

Development record:
    tr03-0005

Important:
    +1 = scored arousal
     0 = scored non-arousal
    -1 = excluded / not scored

    No causal interpretation is permitted.
"""

from pathlib import Path
import csv

import h5py
import numpy as np
import wfdb


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_ROOT = (
    PROJECT_ROOT
    / "Datasets"
    / "raw"
    / "physionet-challenge-2018"
)

RECORD_ID = "tr03-0005"

RECORD_DIR = (
    DATASET_ROOT
    / "training"
    / RECORD_ID
    / RECORD_ID
)

SIGNAL_PATH = RECORD_DIR / RECORD_ID
AROUSAL_MAT_PATH = RECORD_DIR / f"{RECORD_ID}-arousal.mat"

OUTPUT_DIR = PROJECT_ROOT / "research" / "analysis" / "outputs"

FS = 200
OBSERVATION_SECONDS = 60
OBSERVATION_SAMPLES = FS * OBSERVATION_SECONDS

CONTROL_GRID_SECONDS = 5
CONTROL_GRID_SAMPLES = FS * CONTROL_GRID_SECONDS

RANDOM_SEED = 42

EVENT_TYPES = {
    "resp_hypopnea",
    "resp_obstructiveapnea",
    "resp_centralapnea",
    "resp_mixedapnea",
    "arousal_rera",
}

STAGE_NAMES = {
    1: "Wake",
    2: "N1",
    3: "N2",
    4: "N3",
    5: "REM",
}


# ============================================================
# DATA LOADING
# ============================================================

def load_signal():
    record = wfdb.rdrecord(str(SIGNAL_PATH))

    if record.fs != FS:
        raise ValueError(
            f"Expected {FS} Hz, received {record.fs} Hz"
        )

    print(f"Signal loaded: {record.sig_len:,} samples")
    print(f"Channels: {record.n_sig}")
    print(f"Sampling rate: {record.fs} Hz")

    return record



def load_labels_and_stages(expected_samples):
    """
    Load arousal labels and sleep-stage masks from the
    verified nested HDF5 structure.

    Stage codes:
        0 = undefined
        1 = Wake
        2 = N1
        3 = N2
        4 = N3
        5 = REM
    """

    stage_keys = {
        "wake": 1,
        "nonrem1": 2,
        "nonrem2": 3,
        "nonrem3": 4,
        "rem": 5,
        "undefined": 0,
    }

    with h5py.File(AROUSAL_MAT_PATH, "r") as h5:

        data = h5["data"]

        arousals = np.asarray(
            data["arousals"]
        ).reshape(-1)

        sleep_stages = data["sleep_stages"]

        stage_code = np.zeros(
            expected_samples,
            dtype=np.uint8,
        )

        stage_coverage = np.zeros(
            expected_samples,
            dtype=np.uint8,
        )

        for key, code in stage_keys.items():

            mask = np.asarray(
                sleep_stages[key]
            ).reshape(-1).astype(bool)

            if len(mask) != expected_samples:
                raise ValueError(
                    f"Stage length mismatch: {key}"
                )

            stage_coverage += mask.astype(np.uint8)

            if code != 0:
                stage_code[mask] = code

    if len(arousals) != expected_samples:
        raise ValueError("Arousal length mismatch")

    if not set(np.unique(arousals)).issubset(
        {-1.0, 0.0, 1.0}
    ):
        raise ValueError("Unexpected arousal labels")

    if np.any(stage_coverage > 1):
        raise ValueError(
            "Overlapping sleep-stage masks detected"
        )

    print("Arousal labels and sleep stages loaded.")
    print("Sleep-stage structure: VERIFIED")
    print(f"Stage coverage: {np.count_nonzero(stage_coverage):,}")
    print(f"Undefined samples: {np.count_nonzero(stage_code == 0):,}")

    return arousals, stage_code



# ============================================================
# EVENT EXTRACTION
# ============================================================

def parse_events():

    annotations = wfdb.rdann(
        str(SIGNAL_PATH),
        extension="arousal",
    )

    events = []
    active_event = None

    for sample, note in zip(
        annotations.sample,
        annotations.aux_note,
    ):

        note = note.strip()

        if note.startswith("("):

            event_type = note[1:]

            if event_type in EVENT_TYPES:

                if active_event is not None:
                    raise ValueError(
                        "Unexpected nested event annotation"
                    )

                active_event = {
                    "type": event_type,
                    "start": int(sample),
                }

        elif note.endswith(")"):

            event_type = note[:-1]

            if (
                active_event is not None
                and active_event["type"] == event_type
            ):

                start = active_event["start"]
                end = int(sample)

                if end <= start:
                    raise ValueError(
                        "Invalid event interval"
                    )

                events.append({
                    "type": event_type,
                    "start": start,
                    "end": end,
                })

                active_event = None

    if active_event is not None:
        raise ValueError(
            "Unclosed event annotation detected"
        )

    return sorted(events, key=lambda x: x["start"])


# ============================================================
# AROUSAL ONSET DETECTION
# ============================================================

def build_arousal_onsets(arousals):

    previous = np.r_[
        0,
        arousals[:-1],
    ]

    return np.flatnonzero(
        (arousals == 1)
        & (previous != 1)
    )


def has_arousal_after(
    start,
    arousal_onsets,
    sample_count,
):

    endpoint = start + sample_count

    index = np.searchsorted(
        arousal_onsets,
        start,
        side="right",
    )

    return (
        index < len(arousal_onsets)
        and arousal_onsets[index] <= endpoint
    )


# ============================================================
# EVENT OCCUPANCY
# ============================================================

def build_event_occupancy(events, sample_count):

    occupied = np.zeros(
        sample_count,
        dtype=bool,
    )

    for event in events:
        occupied[
            event["start"]:event["end"]
        ] = True

    return occupied


# ============================================================
# EVENT ELIGIBILITY
# ============================================================

def evaluate_events(
    events,
    arousals,
    stage_code,
    event_occupancy,
    arousal_onsets,
):

    sample_count = len(arousals)

    results = []

    for event_index, event in enumerate(events):

        start = event["start"]
        end = event["end"]

        follow_end = end + OBSERVATION_SAMPLES

        result = {
            **event,
            "event_index": event_index,
            "stage": None,
            "eligible": False,
            "arousal_observed": False,
            "control_start": None,
            "matched": False,
            "reason": "",
        }

        if follow_end >= sample_count:
            result["reason"] = "INSUFFICIENT_RECORDING"
            results.append(result)
            continue

        if np.any(
            arousals[end:follow_end + 1] == -1
        ):
            result["reason"] = "EXCLUDED_LABEL"
            results.append(result)
            continue
        
        if arousals[end] != 0:
            result["reason"] = "AROUSAL_ACTIVE_AT_EVENT_END"
            results.append(result)
            continue

        # Exclude another physiological event inside
        # the post-event observation interval.

        if np.any(
            event_occupancy[end:follow_end + 1]
        ):
            result["reason"] = "OTHER_EVENT_IN_FOLLOWUP"
            results.append(result)
            continue

        stage = int(stage_code[end])

        if stage == 0:
            result["reason"] = "UNDEFINED_SLEEP_STAGE"
            results.append(result)
            continue

        result["stage"] = STAGE_NAMES[stage]

        result["eligible"] = True

        result["arousal_observed"] = has_arousal_after(
            end,
            arousal_onsets,
            OBSERVATION_SAMPLES,
        )

        results.append(result)

    return results


# ============================================================
# DETERMINISTIC CONTROL SELECTION
# ============================================================

def select_controls(
    event_results,
    arousals,
    stage_code,
    event_occupancy,
    arousal_onsets,
):

    rng = np.random.default_rng(RANDOM_SEED)

    sample_count = len(arousals)

    # Prefix sums permit fast interval validation.

    excluded_prefix = np.r_[
        0,
        np.cumsum(
            (arousals == -1).astype(np.int32)
        ),
    ]

    event_prefix = np.r_[
        0,
        np.cumsum(
            event_occupancy.astype(np.int32)
        ),
    ]

    # Candidate controls begin at deterministic 5-second
    # intervals, starting from the beginning of the record.

    candidate_starts = np.arange(
        0,
        sample_count - OBSERVATION_SAMPLES,
        CONTROL_GRID_SAMPLES,
        dtype=np.int64,
    )

    selected_occupancy = np.zeros(
        sample_count,
        dtype=bool,
    )

    controls = []

    # Shuffle event order deterministically to avoid
    # always giving early events first access to controls.

    eligible_indices = [
        i for i, result in enumerate(event_results)
        if result["eligible"]
    ]

    processing_order = rng.permutation(
        eligible_indices
    )

    for event_index in processing_order:

        event = event_results[event_index]

        matching = candidate_starts[
            stage_code[candidate_starts] ==
            next(
                code for code, name in STAGE_NAMES.items()
                if name == event["stage"]
            )
        ]

        if len(matching) == 0:
            continue

        matching = rng.permutation(matching)

        selected_start = None

        for control_start in matching:

            control_end = (
                int(control_start)
                + OBSERVATION_SAMPLES
            )

            # A control must start in scored non-arousal.

            if arousals[control_start] != 0:
                continue

            # Entire observation interval must be scored.

            excluded_count = (
                excluded_prefix[control_end + 1]
                - excluded_prefix[control_start]
            )

            if excluded_count != 0:
                continue

            # No annotated physiological event may
            # intersect the control observation interval.

            event_count = (
                event_prefix[control_end + 1]
                - event_prefix[control_start]
            )

            if event_count != 0:
                continue

            # Do not reuse overlapping control windows.

            if np.any(
                selected_occupancy[
                    control_start:control_end + 1
                ]
            ):
                continue

            selected_start = int(control_start)
            break

        if selected_start is None:
            continue

        selected_end = (
            selected_start + OBSERVATION_SAMPLES
        )

        selected_occupancy[
            selected_start:selected_end + 1
        ] = True

        outcome = has_arousal_after(
            selected_start,
            arousal_onsets,
            OBSERVATION_SAMPLES,
        )

        event["control_start"] = selected_start
        event["matched"] = True

        controls.append({
            "event_index": event_index,
            "event_type": event["type"],
            "control_start": selected_start,
            "control_end": selected_end,
            "stage": event["stage"],
            "arousal_observed": outcome,
        })

    return controls


# ============================================================
# SUMMARY
# ============================================================

def calculate_summary(event_results, controls):

    summaries = []

    event_types = sorted(EVENT_TYPES)

    for event_type in event_types:

        matched_events = [
            e for e in event_results
            if e["type"] == event_type
            and e["matched"]
        ]

        matched_controls = [
            c for c in controls
            if c["event_type"] == event_type
        ]

        event_count = len(matched_events)
        control_count = len(matched_controls)

        event_positive = sum(
            e["arousal_observed"]
            for e in matched_events
        )

        control_positive = sum(
            c["arousal_observed"]
            for c in matched_controls
        )

        event_rate = (
            event_positive / event_count
            if event_count else None
        )

        control_rate = (
            control_positive / control_count
            if control_count else None
        )

        difference = (
            event_rate - control_rate
            if event_rate is not None
            and control_rate is not None
            else None
        )

        enrichment = (
            event_rate / control_rate
            if event_rate is not None
            and control_rate not in (None, 0)
            else None
        )

        summaries.append({
            "event_type": event_type,
            "matched_events": event_count,
            "event_arousals": event_positive,
            "event_rate": event_rate,
            "matched_controls": control_count,
            "control_arousals": control_positive,
            "control_rate": control_rate,
            "absolute_difference": difference,
            "relative_enrichment": enrichment,
        })

    return summaries


# ============================================================
# CSV OUTPUT
# ============================================================

def write_csv(path, rows):

    if not rows:
        print(f"No rows to write: {path.name}")
        return

    with path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys()),
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 65)
    print("SYMBIONT - PHASE 1")
    print("BASELINE VS CONTROL ANALYSIS")
    print("=" * 65)

    record = load_signal()

    arousals, stage_code = load_labels_and_stages(
        record.sig_len
    )

    events = parse_events()

    print(f"\nParsed events: {len(events)}")

    event_occupancy = build_event_occupancy(
        events,
        record.sig_len,
    )

    arousal_onsets = build_arousal_onsets(arousals)

    event_results = evaluate_events(
        events,
        arousals,
        stage_code,
        event_occupancy,
        arousal_onsets,
    )

    eligible_count = sum(
        result["eligible"]
        for result in event_results
    )

    print(f"Eligible events: {eligible_count}")

    controls = select_controls(
        event_results,
        arousals,
        stage_code,
        event_occupancy,
        arousal_onsets,
    )

    matched_count = sum(
        result["matched"]
        for result in event_results
    )

    print(f"Matched events: {matched_count}")
    print(f"Selected controls: {len(controls)}")

    summaries = calculate_summary(
        event_results,
        controls,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_csv(
        OUTPUT_DIR / f"{RECORD_ID}_events.csv",
        event_results,
    )

    write_csv(
        OUTPUT_DIR / f"{RECORD_ID}_controls.csv",
        controls,
    )

    write_csv(
        OUTPUT_DIR / f"{RECORD_ID}_summary.csv",
        summaries,
    )

    print("\n" + "=" * 65)
    print("EVENT VS CONTROL RESULTS")
    print("=" * 65)

    for row in summaries:

        event_rate = (
            f"{row['event_rate']:.2%}"
            if row["event_rate"] is not None
            else "N/A"
        )

        control_rate = (
            f"{row['control_rate']:.2%}"
            if row["control_rate"] is not None
            else "N/A"
        )

        print(
            f"{row['event_type']:<26}"
            f"{row['matched_events']:>8}"
            f"{event_rate:>12}"
            f"{row['matched_controls']:>10}"
            f"{control_rate:>12}"
        )

    print("\nFiles saved:")
    print(OUTPUT_DIR)

    print("\nInterpretation:")
    print("DESCRIPTIVE ONLY - NO CAUSAL INFERENCE.")

    print("\nSingle-record analysis complete.")


if __name__ == "__main__":
    main()
