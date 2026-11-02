import os
from collections import Counter, defaultdict

import mne


DATASET_ROOT = r"S:\Symbiont\Datasets\raw\sleep-edfx-1.0.0\sleep-edf-database-expanded-1.0.0"


def find_hypnogram(subset_path, base):
    prefix = base[:-1]

    candidates = [
        f
        for f in os.listdir(subset_path)
        if f.startswith(prefix) and f.endswith("-Hypnogram.edf")
    ]

    if len(candidates) == 1:
        return os.path.join(subset_path, candidates[0])

    if len(candidates) == 0:
        return None

    raise RuntimeError(
        f"Multiple hypnograms found for {base}: {candidates}"
    )


def find_pairs():
    pairs = []

    for subset in ["sleep-cassette", "sleep-telemetry"]:

        subset_path = os.path.join(
            DATASET_ROOT,
            subset
        )

        for filename in sorted(os.listdir(subset_path)):

            if not filename.endswith("-PSG.edf"):
                continue

            base = filename[:-8]

            hypnogram = find_hypnogram(
                subset_path,
                base
            )

            if hypnogram is not None:
                pairs.append(
                    (
                        subset,
                        base,
                        hypnogram
                    )
                )

    return pairs


def main():

    pairs = find_pairs()

    print("=" * 70)
    print("SYMBIONT ANNOTATION DURATION STRUCTURE AUDIT")
    print("=" * 70)

    print(
        f"Records: {len(pairs)}"
    )

    # --------------------------------------------------------------
    # Duration distribution by stage
    # --------------------------------------------------------------

    stage_durations = defaultdict(Counter)

    # --------------------------------------------------------------
    # Record-level examples
    # --------------------------------------------------------------

    example_records = {}

    for subset, record, hypnogram_path in pairs:

        annotations = mne.read_annotations(
            hypnogram_path
        )

        for onset, duration, description in zip(
            annotations.onset,
            annotations.duration,
            annotations.description
        ):

            duration = round(
                float(duration),
                6
            )

            stage_durations[
                description
            ][duration] += 1

            if description not in example_records:
                example_records[description] = []

            if len(example_records[description]) < 10:
                example_records[description].append(
                    (
                        subset,
                        record,
                        onset,
                        duration
                    )
                )

    # --------------------------------------------------------------
    # Print duration distribution
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print("ANNOTATION DURATION DISTRIBUTION")
    print("=" * 70)

    for stage in sorted(stage_durations):

        counter = stage_durations[stage]

        total_annotations = sum(
            counter.values()
        )

        print()
        print(
            f"{stage}"
        )

        print(
            f"Total annotations: {total_annotations}"
        )

        print(
            "Durations:"
        )

        for duration, count in counter.most_common():

            print(
                f"  {duration:>10.2f} sec : {count:>6}"
            )

    # --------------------------------------------------------------
    # Exact 30-sec percentage
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print("30-SECOND REPRESENTATION")
    print("=" * 70)

    for stage in sorted(stage_durations):

        counter = stage_durations[stage]

        total = sum(
            counter.values()
        )

        exact_30 = counter.get(
            30.0,
            0
        )

        percentage = (
            exact_30 / total * 100
            if total
            else 0
        )

        print(
            f"{stage:<20} "
            f"{exact_30:>6}/{total:<6} "
            f"({percentage:>6.2f}%)"
        )

    # --------------------------------------------------------------
    # Example annotations
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print("EXAMPLE ANNOTATIONS")
    print("=" * 70)

    for stage in sorted(example_records):

        print()
        print(stage)

        for (
            subset,
            record,
            onset,
            duration
        ) in example_records[stage]:

            print(
                f"  {subset:<15} "
                f"{record:<10} "
                f"onset={onset:>10.2f} "
                f"duration={duration:>10.2f}"
            )

    print()
    print("=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()