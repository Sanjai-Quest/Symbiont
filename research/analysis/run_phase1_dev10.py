"""
Symbiont - Phase 1
10-Record Development Run

Purpose:
    Run the validated Phase 1 event-to-arousal proximity analysis
    across the fixed 10-record development subset.

This script does NOT change the analysis methodology.
It reuses the same deterministic rules validated on tr03-0005.

Output:
    Console summary only.

Development subset:
    research/reconnaissance/physionet2018_dev10_records.txt
"""

from pathlib import Path

import h5py
import numpy as np
import wfdb


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_ROOT = (
    PROJECT_ROOT
    / "Datasets"
    / "raw"
    / "physionet-challenge-2018"
)

MANIFEST_PATH = (
    PROJECT_ROOT
    / "research"
    / "reconnaissance"
    / "physionet2018_dev10_records.txt"
)

FS = 200.0
MAX_POST_GAP_SECONDS = 60.0
MAX_POST_GAP_SAMPLES = int(MAX_POST_GAP_SECONDS * FS)

POST_WINDOWS = [
    (0, 5, "0-5s"),
    (5, 10, ">5-10s"),
    (10, 20, ">10-20s"),
    (20, 30, ">20-30s"),
    (30, 60, ">30-60s"),
]

EVENT_TYPES = {
    "resp_hypopnea",
    "resp_obstructiveapnea",
    "resp_centralapnea",
    "resp_mixedapnea",
    "arousal_rera",
}


def load_manifest():
    """Load the fixed 10-record development manifest."""

    records = []

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            records.append(line)

    return records


def get_record_paths(record_path):
    """Return local signal and arousal paths for one manifest entry."""

    parts = Path(record_path).parts

    record_id = parts[-1]

    record_dir = (
        DATASET_ROOT
        / Path(*parts).parent
        / record_id
    )

    signal_path = record_dir / record_id
    arousal_path = record_dir / f"{record_id}-arousal.mat"

    return record_id, signal_path, arousal_path


def load_record(record_path):
    """Load signal and arousal labels."""

    record_id, signal_path, arousal_path = get_record_paths(
        record_path
    )

    raw = wfdb.rdrecord(str(signal_path))

    if raw.fs != FS:
        raise ValueError(
            f"{record_id}: sampling rate {raw.fs} != {FS}"
        )

    with h5py.File(arousal_path, "r") as f:
        labels = np.asarray(
            f["data"]["arousals"]
        ).reshape(-1)

    if raw.p_signal.shape[0] != len(labels):
        raise ValueError(
            f"{record_id}: signal/label length mismatch"
        )

    unique_values = set(np.unique(labels))

    if not unique_values.issubset({-1.0, 0.0, 1.0}):
        raise ValueError(
            f"{record_id}: unexpected arousal labels "
            f"{sorted(unique_values)}"
        )

    return record_id, raw, labels


def build_arousal_regions(labels):
    """Build contiguous +1 arousal regions."""

    regions = []

    in_region = False
    start = None

    for i, value in enumerate(labels):

        if value == 1 and not in_region:
            start = i
            in_region = True

        elif value != 1 and in_region:
            regions.append((start, i))
            in_region = False

    if in_region:
        regions.append((start, len(labels)))

    return regions


def parse_events(signal_path):
    """Parse verified start/end physiological events."""

    annotation = wfdb.rdann(
        str(signal_path),
        extension="arousal",
    )

    events = []
    active = {}

    for sample, note in zip(
        annotation.sample,
        annotation.aux_note,
    ):

        if not note:
            continue

        note = note.strip()

        if note.startswith("("):

            event_type = note[1:]

            if event_type in EVENT_TYPES:
                active[event_type] = sample

        elif note.endswith(")"):

            event_type = note[:-1]

            if event_type in active:

                events.append(
                    {
                        "type": event_type,
                        "start": active[event_type],
                        "end": sample,
                    }
                )

                del active[event_type]

    return events


def calculate_overlap(event, regions):
    """Return overlapping arousal duration in seconds."""

    event_start = event["start"]
    event_end = event["end"]

    overlap_samples = 0

    for arousal_start, arousal_end in regions:

        overlap_start = max(
            event_start,
            arousal_start,
        )

        overlap_end = min(
            event_end,
            arousal_end,
        )

        if overlap_start < overlap_end:
            overlap_samples += (
                overlap_end - overlap_start
            )

    return overlap_samples / FS


def find_post_arousal(event, regions):
    """Find first arousal beginning within 60 seconds after event."""

    event_end = event["end"]

    for arousal_start, arousal_end in regions:

        if arousal_start >= event_end:

            gap_samples = (
                arousal_start - event_end
            )

            if gap_samples <= MAX_POST_GAP_SAMPLES:
                return (
                    arousal_start,
                    arousal_end,
                )

            return None

    return None


def classify_post_window(gap_seconds):
    """Assign the predefined post-event attribution window."""

    if gap_seconds is None:
        return None

    for lower, upper, label in POST_WINDOWS:

        if lower == 0:
            if 0 <= gap_seconds <= upper:
                return label

        elif lower < gap_seconds <= upper:
            return label

    return None


def analyze_record(record_path):
    """Run complete Phase 1 analysis for one record."""

    record_id, raw, labels = load_record(
        record_path
    )

    regions = build_arousal_regions(labels)

    events = parse_events(
        get_record_paths(record_path)[1]
    )

    results = []

    for event in events:

        overlap_seconds = calculate_overlap(
            event,
            regions,
        )

        next_region = find_post_arousal(
            event,
            regions,
        )

        post_gap_seconds = None
        post_window = None

        if next_region is not None:

            post_gap_seconds = (
                next_region[0] - event["end"]
            ) / FS

            post_window = classify_post_window(
                post_gap_seconds
            )

        results.append(
            {
                "type": event["type"],
                "start": event["start"],
                "end": event["end"],
                "overlap_seconds": overlap_seconds,
                "post_gap_seconds": post_gap_seconds,
                "post_window": post_window,
            }
        )

    return {
        "record_id": record_id,
        "samples": raw.p_signal.shape[0],
        "channels": raw.p_signal.shape[1],
        "arousal_regions": len(regions),
        "events": results,
    }


def summarize(results):
    """Print deterministic aggregate results."""

    total_events = 0
    total_overlap_events = 0
    total_post_events = 0

    event_counts = {}
    overlap_counts = {}
    post_counts = {}

    for record in results:

        for event in record["events"]:

            event_type = event["type"]

            total_events += 1

            event_counts[event_type] = (
                event_counts.get(event_type, 0) + 1
            )

            if event["overlap_seconds"] > 0:

                total_overlap_events += 1

                overlap_counts[event_type] = (
                    overlap_counts.get(event_type, 0) + 1
                )

            if event["post_window"] is not None:

                total_post_events += 1

                key = (
                    event_type,
                    event["post_window"],
                )

                post_counts[key] = (
                    post_counts.get(key, 0) + 1
                )

    print("\n" + "=" * 60)
    print("PHASE 1 - 10 RECORD SUMMARY")
    print("=" * 60)

    print(f"Records analyzed: {len(results)}")
    print(f"Total events: {total_events}")
    print(
        f"Events with direct arousal overlap: "
        f"{total_overlap_events}"
    )
    print(
        f"Events with post-event arousal <=60s: "
        f"{total_post_events}"
    )

    print("\nEvent counts")
    print("-" * 60)

    for event_type in sorted(event_counts):

        count = event_counts[event_type]

        overlap = overlap_counts.get(
            event_type,
            0,
        )

        print(
            f"{event_type:<28}"
            f"{count:>5} events"
            f" | overlap: {overlap:>5}"
        )

    print("\nPost-event windows")
    print("-" * 60)

    for event_type in sorted(event_counts):

        print(f"\n{event_type}")

        for _, _, label in POST_WINDOWS:

            count = post_counts.get(
                (event_type, label),
                0,
            )

            print(
                f"  {label:<10}: {count}"
            )


def main():

    print("=" * 60)
    print("SYMBIONT - PHASE 1")
    print("10-Record Development Run")
    print("=" * 60)

    records = load_manifest()

    print(
        f"Manifest records: {len(records)}"
    )

    if len(records) != 10:
        raise ValueError(
            "Development manifest must contain exactly 10 records."
        )

    results = []

    for index, record_path in enumerate(
        records,
        start=1,
    ):

        print(
            f"\n[{index}/10] {record_path}"
        )

        result = analyze_record(
            record_path
        )

        results.append(result)

        print(
            f"  Samples: {result['samples']}"
        )

        print(
            f"  Channels: {result['channels']}"
        )

        print(
            f"  Arousal regions: "
            f"{result['arousal_regions']}"
        )

        print(
            f"  Events: "
            f"{len(result['events'])}"
        )

        if result["channels"] != 13:
            raise ValueError(
                f"{result['record_id']}: "
                f"expected 13 channels."
            )

    summarize(results)

    print("\n" + "=" * 60)
    print("10-RECORD RUN COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()