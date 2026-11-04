"""
Symbiont - Phase 1
Event-to-Arousal Temporal Proximity Analysis

Purpose:
    Analyze the temporal relationship between annotated physiological
    events and scored arousal regions.

Development strategy:
    1. Load one validated PhysioNet record.
    2. Load arousal labels.
    3. Build contiguous arousal regions.
    4. Parse annotated physiological events.
    5. Measure overlap and temporal proximity.
    6. Validate first on tr03-0005.

Important:
    - arousals == +1  -> scored arousal
    - arousals == 0   -> scored non-arousal
    - arousals == -1  -> excluded / not scored
    - -1 must NOT be treated as a negative class.
"""

from pathlib import Path

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

FS = 200.0

POST_WINDOWS = [
    (0, 5),
    (5, 10),
    (10, 20),
    (20, 30),
    (30, 60),
]


# ============================================================
# LOAD SIGNAL
# ============================================================

def load_signal():
    """Load the WFDB PSG record and return the record object."""

    record = wfdb.rdrecord(str(SIGNAL_PATH))

    if record.fs != FS:
        raise ValueError(
            f"Unexpected sampling rate: {record.fs} Hz "
            f"(expected {FS} Hz)"
        )

    print("Signal loaded successfully.")
    print(f"Sampling rate: {record.fs} Hz")
    print(f"Samples: {record.sig_len}")
    print(f"Channels: {record.n_sig}")

    return record


# ============================================================
# LOAD AROUSAL LABELS
# ============================================================

def load_arousal_labels():
    """
    Load the authoritative arousal target vector.

    Values:
        +1 = arousal
         0 = scored non-arousal
        -1 = excluded / not scored
    """

    with h5py.File(AROUSAL_MAT_PATH, "r") as h5:
        arousals = np.asarray(h5["data"]["arousals"]).reshape(-1)

    unique_values = np.unique(arousals)

    expected_values = {-1.0, 0.0, 1.0}

    if not set(unique_values).issubset(expected_values):
        raise ValueError(
            f"Unexpected arousal values: {unique_values}"
        )

    print("\nArousal labels loaded successfully.")
    print(f"Samples: {len(arousals)}")
    print(f"Unique values: {unique_values}")

    return arousals


# ============================================================
# BUILD AROUSAL REGIONS
# ============================================================

def build_arousal_regions(arousals):
    """
    Convert individual +1 samples into contiguous arousal regions.

    Returns:
        List of tuples:
            (start_sample, end_sample)

    Interval convention:
        [start, end)

    Therefore:
        duration = end - start
    """

    arousal_indices = np.flatnonzero(arousals == 1)

    if len(arousal_indices) == 0:
        return []

    breaks = np.where(np.diff(arousal_indices) > 1)[0]

    starts = np.r_[
        arousal_indices[0],
        arousal_indices[breaks + 1],
    ]

    ends = np.r_[
        arousal_indices[breaks] + 1,
        arousal_indices[-1] + 1,
    ]

    regions = list(zip(starts, ends))

    return regions


# ============================================================
# PARSE EVENT ANNOTATIONS
# ============================================================

def parse_events():
    """
    Parse paired physiological event annotations from the
    WFDB .arousal annotation file.

    Currently recognized event types:

        resp_hypopnea
        resp_obstructiveapnea
        resp_centralapnea
        resp_mixedapnea
        arousal_rera

    Events are represented using [start, end) sample intervals.
    """

    annotation_path = str(SIGNAL_PATH)

    annotations = wfdb.rdann(
        annotation_path,
        extension="arousal",
    )

    events = []

    active_event = None

    for sample, note in zip(
        annotations.sample,
        annotations.aux_note,
    ):

        note = note.strip()

        # Event start
        if note.startswith("("):

            event_type = note[1:]

            if event_type in {
                "resp_hypopnea",
                "resp_obstructiveapnea",
                "resp_centralapnea",
                "resp_mixedapnea",
                "arousal_rera",
            }:
                active_event = {
                    "type": event_type,
                    "start": int(sample),
                }

        # Event end
        elif note.endswith(")"):

            event_type = note[:-1]

            if (
                active_event is not None
                and active_event["type"] == event_type
            ):
                events.append(
                    {
                        "type": event_type,
                        "start": active_event["start"],
                        "end": int(sample),
                    }
                )

                active_event = None

    return events


# ============================================================
# OVERLAP ANALYSIS
# ============================================================

def calculate_overlap(event, arousal_regions):
    """
    Determine whether an event overlaps a scored arousal region.

    Returns:
        Number of arousal samples overlapping the event.
    """

    event_start = event["start"]
    event_end = event["end"]

    overlap_samples = 0

    for arousal_start, arousal_end in arousal_regions:

        overlap_start = max(event_start, arousal_start)
        overlap_end = min(event_end, arousal_end)

        if overlap_start < overlap_end:
            overlap_samples += overlap_end - overlap_start

    return overlap_samples


# ============================================================
# TEMPORAL PROXIMITY
# ============================================================

def calculate_proximity(event, arousal_regions):
    event_start = event["start"]
    event_end = event["end"]

    MAX_POST_GAP_SECONDS = 60.0
    MAX_POST_GAP_SAMPLES = int(MAX_POST_GAP_SECONDS * FS)

    previous_region = None
    next_region = None

    for arousal_start, arousal_end in arousal_regions:

        if arousal_end <= event_start:
            previous_region = (arousal_start, arousal_end)

        elif arousal_start >= event_end:
            gap_samples = arousal_start - event_end

            if gap_samples <= MAX_POST_GAP_SAMPLES:
                next_region = (arousal_start, arousal_end)

            break

    pre_gap_seconds = None
    post_gap_seconds = None

    if previous_region is not None:
        pre_gap_seconds = (
            event_start - previous_region[1]
        ) / FS

    if next_region is not None:
        post_gap_seconds = (
            next_region[0] - event_end
        ) / FS

    return {
        "pre_gap_seconds": pre_gap_seconds,
        "post_gap_seconds": post_gap_seconds,
    }


# ============================================================
# WINDOW CLASSIFICATION
# ============================================================

def classify_post_window(gap_seconds):
    """
    Assign a post-event arousal gap to the predefined window.
    """

    if gap_seconds is None:
        return None

    for lower, upper in POST_WINDOWS:

        if lower == 0:
            if 0 <= gap_seconds <= upper:
                return f"0-5s"

        elif lower < gap_seconds <= upper:
            return f">{lower}-{upper}s"

    return None


# ============================================================
# MAIN ANALYSIS
# ============================================================

def main():

    print("=" * 60)
    print("SYMBIONT - PHASE 1")
    print("Event-to-Arousal Temporal Proximity Analysis")
    print("=" * 60)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    record = load_signal()

    arousals = load_arousal_labels()

    if len(arousals) != record.sig_len:
        raise ValueError(
            "Signal and arousal label lengths do not match."
        )

    # --------------------------------------------------------
    # Build arousal regions
    # --------------------------------------------------------

    arousal_regions = build_arousal_regions(arousals)

    print(f"\nArousal regions: {len(arousal_regions)}")

    # --------------------------------------------------------
    # Parse events
    # --------------------------------------------------------

    events = parse_events()

    print(f"Parsed events: {len(events)}")

    # --------------------------------------------------------
    # Analyze events
    # --------------------------------------------------------

    results = []

    for event in events:

        overlap_samples = calculate_overlap(
            event,
            arousal_regions,
        )

        proximity = calculate_proximity(
            event,
            arousal_regions,
        )

        result = {
            **event,
            "overlap_samples": overlap_samples,
            "overlap_seconds": overlap_samples / FS,
            "pre_gap_seconds": proximity["pre_gap_seconds"],
            "post_gap_seconds": proximity["post_gap_seconds"],
            "post_window": classify_post_window(
                proximity["post_gap_seconds"]
            ),
        }

        results.append(result)

    # --------------------------------------------------------
    # Print first results for manual inspection
    # --------------------------------------------------------

    print("\nFirst 10 analyzed events:")
    print("-" * 60)

    for result in results[:10]:

        print(
            f"{result['type']:25s} "
            f"start={result['start']:8d} "
            f"end={result['end']:8d} "
            f"overlap={result['overlap_seconds']:7.3f}s "
            f"pre={result['pre_gap_seconds']} "
            f"post={result['post_gap_seconds']} "
            f"window={result['post_window']}"
        )

    print("\nAnalysis completed successfully.")
    print(f"Total analyzed events: {len(results)}")


if __name__ == "__main__":
    main()