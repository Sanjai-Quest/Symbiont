from pathlib import Path
from collections import defaultdict

import h5py
import numpy as np
import wfdb


ROOT = Path("Datasets/raw/physionet-challenge-2018/training")


def parse_events(record_dir: Path):
    record_id = record_dir.name
    base = record_dir / record_id

    annotation = wfdb.rdann(
        str(base),
        "arousal",
    )

    events = []
    open_events = {}

    for sample, note in zip(
        annotation.sample,
        annotation.aux_note,
    ):
        if not note:
            continue

        note = note.strip()

        if note.startswith("("):
            event_type = note[1:]
            open_events[event_type] = sample

        elif note.endswith(")"):
            event_type = note[:-1]

            if event_type in open_events:
                start = open_events.pop(event_type)
                end = sample

                if end >= start:
                    events.append(
                        {
                            "type": event_type,
                            "start": int(start),
                            "end": int(end),
                        }
                    )

    return events


def analyze_record(record_dir: Path):
    record_id = record_dir.name
    base = record_dir / record_id
    arousal_mat = record_dir / f"{record_id}-arousal.mat"

    record = wfdb.rdrecord(str(base))
    fs = record.fs

    events = parse_events(record_dir)

    with h5py.File(arousal_mat, "r") as f:
        arousals = np.asarray(
            f["data"]["arousals"]
        ).ravel()

    results = []

    for event in events:
        start = event["start"]
        end = event["end"]

        # Event intervals are treated as [start, end).
        event_labels = arousals[start:end]

        event_length = len(event_labels)

        arousal_samples = np.sum(
            event_labels == 1
        )

        overlap_pct = (
            arousal_samples / event_length * 100
            if event_length > 0
            else 0
        )

        associated = arousal_samples > 0

        results.append(
            {
                "record_id": record_id,
                "type": event["type"],
                "start": start,
                "end": end,
                "duration_samples": event_length,
                "duration_seconds": event_length / fs,
                "arousal_samples": int(
                    arousal_samples
                ),
                "arousal_overlap_pct": overlap_pct,
                "associated_with_arousal": associated,
            }
        )

    return results


def main():
    record_dirs = sorted(
        p.parent
        for p in ROOT.glob("*/*/*-arousal.mat")
    )

    print(
        f"Development records found: "
        f"{len(record_dirs)}"
    )
    print()

    all_results = []

    for record_dir in record_dirs:
        results = analyze_record(record_dir)
        all_results.extend(results)

    print("=" * 70)
    print("EVENT-TO-AROUSAL OVERLAP ANALYSIS")
    print("=" * 70)

    print(
        f"Total parsed events: "
        f"{len(all_results)}"
    )

    print()

    aggregate = defaultdict(
        lambda: {
            "events": 0,
            "associated": 0,
            "arousal_samples": 0,
            "event_samples": 0,
        }
    )

    for result in all_results:
        event_type = result["type"]

        aggregate[event_type]["events"] += 1

        if result["associated_with_arousal"]:
            aggregate[event_type]["associated"] += 1

        aggregate[event_type][
            "arousal_samples"
        ] += result["arousal_samples"]

        aggregate[event_type][
            "event_samples"
        ] += result["duration_samples"]

    print("EVENT TYPE SUMMARY")
    print()

    for event_type in sorted(aggregate):
        data = aggregate[event_type]

        events = data["events"]
        associated = data["associated"]

        event_association_pct = (
            associated / events * 100
            if events
            else 0
        )

        overlap_pct = (
            data["arousal_samples"]
            / data["event_samples"]
            * 100
            if data["event_samples"]
            else 0
        )

        print(f"{event_type}")
        print(
            f"  TOTAL EVENTS          : {events}"
        )
        print(
            f"  EVENTS WITH AROUSAL   : "
            f"{associated}"
        )
        print(
            f"  EVENT ASSOCIATION %   : "
            f"{event_association_pct:.2f}%"
        )
        print(
            f"  TOTAL EVENT SAMPLES   : "
            f"{data['event_samples']:,}"
        )
        print(
            f"  AROUSAL OVERLAP       : "
            f"{data['arousal_samples']:,}"
        )
        print(
            f"  SAMPLE OVERLAP %      : "
            f"{overlap_pct:.2f}%"
        )
        print()

    print("=" * 70)
    print("RECORD-LEVEL SUMMARY")
    print("=" * 70)

    record_groups = defaultdict(list)

    for result in all_results:
        record_groups[
            result["record_id"]
        ].append(result)

    for record_id in sorted(record_groups):
        results = record_groups[record_id]

        associated = sum(
            r["associated_with_arousal"]
            for r in results
        )

        total = len(results)

        print(
            f"{record_id}: "
            f"{associated}/{total} events "
            f"associated with arousal "
            f"({associated / total * 100:.2f}%)"
        )


if __name__ == "__main__":
    main()