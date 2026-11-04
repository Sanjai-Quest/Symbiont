"""
Symbiont - Phase 1 Diagnostic

Purpose:
    Inspect the temporal relationship between annotated physiological
    events and scored arousal regions for one validation record.

Validation record:
    tr03-0005

This script does NOT calculate final product metrics.
It is only for manual verification of the event/arousal relationship.
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


# ============================================================
# LOAD AROUSAL LABELS
# ============================================================

def load_arousal_labels():
    """Load the authoritative arousal target vector."""

    with h5py.File(AROUSAL_MAT_PATH, "r") as h5:
        arousals = np.asarray(
            h5["data"]["arousals"]
        ).reshape(-1)

    return arousals


# ============================================================
# BUILD AROUSAL REGIONS
# ============================================================

def build_arousal_regions(arousals):
    """
    Convert contiguous +1 samples into [start, end) regions.
    """

    indices = np.flatnonzero(arousals == 1)

    if len(indices) == 0:
        return []

    breaks = np.where(np.diff(indices) > 1)[0]

    starts = np.r_[
        indices[0],
        indices[breaks + 1],
    ]

    ends = np.r_[
        indices[breaks] + 1,
        indices[-1] + 1,
    ]

    return list(zip(starts, ends))


# ============================================================
# PARSE EVENTS
# ============================================================

def parse_events():
    """Parse paired event annotations."""

    annotations = wfdb.rdann(
        str(SIGNAL_PATH),
        extension="arousal",
    )

    valid_event_types = {
        "resp_hypopnea",
        "resp_obstructiveapnea",
        "resp_centralapnea",
        "resp_mixedapnea",
        "arousal_rera",
    }

    events = []
    active_event = None

    for sample, note in zip(
        annotations.sample,
        annotations.aux_note,
    ):

        note = note.strip()

        if note.startswith("("):

            event_type = note[1:]

            if event_type in valid_event_types:
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
# TIME CONVERSION
# ============================================================

def seconds(sample):
    """Convert a sample index to seconds."""

    return sample / FS


def duration_seconds(start, end):
    """Calculate interval duration in seconds."""

    return (end - start) / FS


# ============================================================
# EVENT RELATIONSHIP
# ============================================================

def inspect_event(event, arousal_regions):

    event_start = event["start"]
    event_end = event["end"]

    overlapping = []
    previous = None
    following = None

    for region_start, region_end in arousal_regions:

        # Event overlaps arousal
        if (
            region_start < event_end
            and region_end > event_start
        ):
            overlapping.append(
                (region_start, region_end)
            )

        # Entire arousal region is before event
        elif region_end <= event_start:
            previous = (region_start, region_end)

        # First arousal region after event
        elif (
            region_start >= event_end
            and following is None
        ):
            following = (region_start, region_end)

    return previous, overlapping, following


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print("SYMBIONT - EVENT / AROUSAL DIAGNOSTIC")
    print("=" * 72)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    arousals = load_arousal_labels()
    arousal_regions = build_arousal_regions(arousals)
    events = parse_events()

    print(f"\nRecord: {RECORD_ID}")
    print(f"Sampling rate: {FS} Hz")
    print(f"Arousal regions: {len(arousal_regions)}")
    print(f"Parsed events: {len(events)}")

    # --------------------------------------------------------
    # Print all arousal regions
    # --------------------------------------------------------

    print("\n" + "=" * 72)
    print("AROUSAL REGIONS")
    print("=" * 72)

    for i, (start, end) in enumerate(
        arousal_regions,
        start=1,
    ):

        print(
            f"Arousal {i:02d}: "
            f"samples {start:8d} - {end:8d} | "
            f"time {seconds(start):9.3f}s - "
            f"{seconds(end):9.3f}s | "
            f"duration {duration_seconds(start, end):7.3f}s"
        )

    # --------------------------------------------------------
    # Print all event relationships
    # --------------------------------------------------------

    print("\n" + "=" * 72)
    print("EVENT / AROUSAL RELATIONSHIPS")
    print("=" * 72)

    for i, event in enumerate(events, start=1):

        previous, overlapping, following = inspect_event(
            event,
            arousal_regions,
        )

        print(
            f"\nEvent {i:02d}: {event['type']}"
        )

        print(
            f"  Event interval : "
            f"{seconds(event['start']):9.3f}s - "
            f"{seconds(event['end']):9.3f}s"
        )

        print(
            f"  Event duration : "
            f"{duration_seconds(event['start'], event['end']):7.3f}s"
        )

        # Previous arousal
        if previous is None:
            print("  Previous arousal: NONE")
        else:
            gap = (
                event["start"] - previous[1]
            ) / FS

            print(
                f"  Previous arousal: "
                f"{seconds(previous[0]):9.3f}s - "
                f"{seconds(previous[1]):9.3f}s | "
                f"gap={gap:7.3f}s"
            )

        # Overlap
        if not overlapping:
            print("  Overlapping arousal: NONE")
        else:
            for region in overlapping:

                overlap_start = max(
                    event["start"],
                    region[0],
                )

                overlap_end = min(
                    event["end"],
                    region[1],
                )

                overlap_duration = (
                    overlap_end - overlap_start
                ) / FS

                print(
                    f"  Overlapping arousal: "
                    f"{seconds(region[0]):9.3f}s - "
                    f"{seconds(region[1]):9.3f}s | "
                    f"overlap={overlap_duration:7.3f}s"
                )

        # Following arousal
        if following is None:
            print("  Following arousal: NONE")
        else:
            gap = (
                following[0] - event["end"]
            ) / FS

            print(
                f"  Following arousal: "
                f"{seconds(following[0]):9.3f}s - "
                f"{seconds(following[1]):9.3f}s | "
                f"gap={gap:7.3f}s"
            )


if __name__ == "__main__":
    main()