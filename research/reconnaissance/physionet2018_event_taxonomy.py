from pathlib import Path
from collections import defaultdict

import wfdb


ROOT = Path("Datasets/raw/physionet-challenge-2018/training")


def parse_event_notes(record_dir: Path):
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

        # Event start marker: "(event_name"
        if note.startswith("("):
            event_name = note[1:]

            open_events[event_name] = sample

        # Event end marker: "event_name)"
        elif note.endswith(")"):
            event_name = note[:-1]

            if event_name in open_events:
                start = open_events.pop(event_name)
                end = sample

                if end >= start:
                    events.append(
                        {
                            "type": event_name,
                            "start": start,
                            "end": end,
                            "duration_samples": end - start,
                        }
                    )

    return events, annotation


def analyze_record(record_dir: Path):
    record_id = record_dir.name

    events, annotation = parse_event_notes(
        record_dir
    )

    # Determine sampling rate from the signal.
    record = wfdb.rdrecord(
        str(record_dir / record_id)
    )

    fs = record.fs

    counts = defaultdict(int)
    durations = defaultdict(int)

    for event in events:
        event_type = event["type"]

        counts[event_type] += 1
        durations[event_type] += (
            event["duration_samples"]
        )

    print("=" * 70)
    print(record_id)

    print(
        f"  TOTAL ANNOTATIONS : "
        f"{len(annotation.sample)}"
    )

    print(
        f"  PARSED EVENTS     : "
        f"{len(events)}"
    )

    print()
    print("  EVENT TYPES:")

    for event_type in sorted(counts):
        count = counts[event_type]
        duration_seconds = (
            durations[event_type] / fs
        )

        print(
            f"    {event_type}: "
            f"{count} events | "
            f"{duration_seconds:.2f} sec"
        )

    return counts, durations


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

    aggregate_counts = defaultdict(int)
    aggregate_durations = defaultdict(int)

    for record_dir in record_dirs:
        counts, durations = analyze_record(
            record_dir
        )

        for event_type, count in counts.items():
            aggregate_counts[event_type] += count

        for event_type, duration in durations.items():
            aggregate_durations[event_type] += duration

    print()
    print("=" * 70)
    print("AGGREGATE EVENT TAXONOMY")
    print("=" * 70)

    # All records use 200 Hz in our validated subset.
    fs = 200

    total_events = sum(
        aggregate_counts.values()
    )

    print(
        f"  TOTAL PARSED EVENTS: "
        f"{total_events}"
    )

    print()

    for event_type in sorted(
        aggregate_counts,
        key=lambda x: (
            -aggregate_counts[x],
            x,
        ),
    ):
        count = aggregate_counts[event_type]

        duration_seconds = (
            aggregate_durations[event_type]
            / fs
        )

        print(
            f"  {event_type}: "
            f"{count} events | "
            f"{duration_seconds:.2f} sec"
        )


if __name__ == "__main__":
    main()