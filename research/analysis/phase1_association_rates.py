"""
Symbiont - Phase 1
Association Rate Analysis

Purpose:
    Calculate descriptive temporal association rates from the
    validated 10-record Phase 1 development subset.

This script does not establish causality.

Definitions:
    Associated event:
        An annotated physiological event followed by the beginning
        of a scored arousal within 60 seconds after the event ends.

    Direct overlap:
        A scored arousal overlaps the annotated event interval.

    Post-event windows:
        0-5s
        >5-10s
        >10-20s
        >20-30s
        >30-60s

Important:
    - arousals == +1 -> scored arousal
    - arousals == 0  -> scored non-arousal
    - arousals == -1 -> excluded / not scored
    - -1 is never treated as a negative class.

Current scope:
    Fixed 10-record development subset.

This analysis is descriptive.
It does not establish causality.
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
MAX_POST_GAP_SAMPLES = int(
    MAX_POST_GAP_SECONDS * FS
)

EVENT_TYPES = {
    "resp_hypopnea",
    "resp_obstructiveapnea",
    "resp_centralapnea",
    "resp_mixedapnea",
    "arousal_rera",
}

POST_WINDOWS = [
    (0, 5, "0-5s"),
    (5, 10, ">5-10s"),
    (10, 20, ">10-20s"),
    (20, 30, ">20-30s"),
    (30, 60, ">30-60s"),
]


def load_manifest():
    records = []

    with open(
        MANIFEST_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        for line in f:

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            records.append(line)

    return records


def get_record_paths(record_path):
    parts = Path(record_path).parts
    record_id = parts[-1]

    record_dir = (
        DATASET_ROOT
        / Path(*parts).parent
        / record_id
    )

    signal_path = record_dir / record_id
    arousal_path = (
        record_dir / f"{record_id}-arousal.mat"
    )

    return record_id, signal_path, arousal_path


def load_record(record_path):
    record_id, signal_path, arousal_path = (
        get_record_paths(record_path)
    )

    raw = wfdb.rdrecord(str(signal_path))

    if raw.fs != FS:
        raise ValueError(
            f"{record_id}: unexpected sampling rate "
            f"{raw.fs} Hz"
        )

    with h5py.File(
        arousal_path,
        "r",
    ) as f:

        labels = np.asarray(
            f["data"]["arousals"]
        ).reshape(-1)

    if raw.p_signal.shape[0] != len(labels):
        raise ValueError(
            f"{record_id}: signal and arousal "
            f"length mismatch"
        )

    return (
        record_id,
        signal_path,
        labels,
    )


def build_arousal_regions(labels):
    regions = []

    in_region = False
    start = None

    for index, value in enumerate(labels):

        if value == 1 and not in_region:

            start = index
            in_region = True

        elif value != 1 and in_region:

            regions.append(
                (start, index)
            )

            in_region = False

    if in_region:

        regions.append(
            (start, len(labels))
        )

    return regions


def parse_events(signal_path):
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

    return overlap_samples > 0


def find_post_arousal(event, regions):
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
    (
        record_id,
        signal_path,
        labels,
    ) = load_record(record_path)

    regions = build_arousal_regions(labels)

    events = parse_events(signal_path)

    analyzed = []

    for event in events:

        direct_overlap = calculate_overlap(
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
                next_region[0]
                - event["end"]
            ) / FS

            post_window = classify_post_window(
                post_gap_seconds
            )

        analyzed.append(
            {
                "type": event["type"],
                "direct_overlap": direct_overlap,
                "post_gap_seconds": post_gap_seconds,
                "post_window": post_window,
            }
        )

    return record_id, analyzed


def calculate_rates(all_results):
    event_summary = {}

    for record_id, events in all_results:

        for event in events:

            event_type = event["type"]

            if event_type not in event_summary:

                event_summary[event_type] = {
                    "total": 0,
                    "overlap": 0,
                    "post_60s": 0,
                    "windows": {
                        label: 0
                        for _, _, label
                        in POST_WINDOWS
                    },
                }

            summary = event_summary[event_type]

            summary["total"] += 1

            if event["direct_overlap"]:
                summary["overlap"] += 1

            if event["post_window"] is not None:

                summary["post_60s"] += 1

                summary["windows"][
                    event["post_window"]
                ] += 1

    return event_summary


def print_summary(event_summary):

    print("\n" + "=" * 72)
    print("PHASE 1 - ASSOCIATION RATE SUMMARY")
    print("=" * 72)

    print("-" * 72)

    for event_type in sorted(event_summary):

        summary = event_summary[event_type]

        total = summary["total"]

        overlap_rate = (
            summary["overlap"] / total * 100
        )

        post_rate = (
            summary["post_60s"] / total * 100
        )

        print(
            f"{event_type:<28}"
            f"{total:>6}"
            f"{summary['overlap']:>10}"
            f"{overlap_rate:>10.2f}%"
            f"{summary['post_60s']:>11}"
            f"{post_rate:>10.2f}%"
        )

    print("\nPost-event window distribution")
    print("-" * 72)

    for event_type in sorted(event_summary):

        summary = event_summary[event_type]

        print(f"\n{event_type}")

        for _, _, label in POST_WINDOWS:

            count = summary["windows"][label]

            print(
                f"  {label:<10}: {count}"
            )


def main():

    print("=" * 72)
    print("SYMBIONT - PHASE 1")
    print("Association Rate Analysis")
    print("=" * 72)

    records = load_manifest()

    if len(records) != 10:

        raise ValueError(
            "Expected exactly 10 development records."
        )

    all_results = []

    for index, record_path in enumerate(
        records,
        start=1,
    ):

        print(
            f"[{index}/10] "
            f"{record_path}"
        )

        record_id, events = analyze_record(
            record_path
        )

        print(
            f"  Events analyzed: "
            f"{len(events)}"
        )

        all_results.append(
            (
                record_id,
                events,
            )
        )

    event_summary = calculate_rates(
        all_results
    )

    print_summary(
        event_summary
    )

    print("\n" + "=" * 72)
    print("ASSOCIATION RATE ANALYSIS COMPLETE")
    print("=" * 72)

    print(
        "\nInterpretation status:"
    )

    print(
        "DESCRIPTIVE ONLY - "
        "No causal inference."
    )


if __name__ == "__main__":
    main()