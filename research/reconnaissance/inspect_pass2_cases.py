import os
import mne

DATASET_ROOT = r"S:\Symbiont\Datasets\raw\sleep-edfx-1.0.0\sleep-edf-database-expanded-1.0.0"

CASES = [
    ("sleep-cassette", "SC4001E0"),
    ("sleep-cassette", "SC4592G0"),
    ("sleep-telemetry", "ST7192J0"),
    ("sleep-telemetry", "ST7121J0"),
]


def find_file(subset_path, record, suffix):
    prefix = record[:-1]

    candidates = [
        filename
        for filename in os.listdir(subset_path)
        if filename.startswith(prefix) and filename.endswith(suffix)
    ]

    if len(candidates) == 0:
        raise FileNotFoundError(
            f"No file found for {record} with suffix {suffix}"
        )

    if len(candidates) > 1:
        raise RuntimeError(
            f"Multiple files found for {record} with suffix {suffix}: "
            f"{candidates}"
        )

    return os.path.join(subset_path, candidates[0])


print("=" * 80)
print("PASS 2 TARGETED CASE INSPECTION")
print("=" * 80)


for subset, record in CASES:

    print()
    print("=" * 80)
    print(f"{subset} / {record}")
    print("=" * 80)

    subset_path = os.path.join(DATASET_ROOT, subset)

    psg_path = find_file(
        subset_path,
        record,
        "-PSG.edf"
    )

    hypnogram_path = find_file(
        subset_path,
        record,
        "-Hypnogram.edf"
    )

    print("PSG file:")
    print(" ", os.path.basename(psg_path))

    print("Hypnogram file:")
    print(" ", os.path.basename(hypnogram_path))

    raw = mne.io.read_raw_edf(
        psg_path,
        preload=False,
        verbose=False
    )

    annotations = mne.read_annotations(
        hypnogram_path
    )

    psg_duration = raw.times[-1]

    sorted_annotations = sorted(
        zip(
            annotations.onset,
            annotations.duration,
            annotations.description
        ),
        key=lambda x: x[0]
    )

    print()
    print("PSG duration:", psg_duration, "seconds")
    print("PSG duration:", psg_duration / 3600, "hours")

    print("Annotation count:", len(sorted_annotations))

    if sorted_annotations:
        first = sorted_annotations[0]
        last = sorted_annotations[-1]

        print()
        print("FIRST ANNOTATION")
        print("  Onset:", first[0])
        print("  Duration:", first[1])
        print("  End:", first[0] + first[1])
        print("  Description:", repr(first[2]))

        print()
        print("LAST ANNOTATION")
        print("  Onset:", last[0])
        print("  Duration:", last[1])
        print("  End:", last[0] + last[1])
        print("  Description:", repr(last[2]))

    print()
    print("Unique labels:")
    for label in sorted(set(annotations.description)):
        print(" ", repr(label))

    annotation_end = max(
        onset + duration
        for onset, duration, _ in sorted_annotations
    )

    print()
    print("Hypnogram last annotation end:", annotation_end)
    print("Hypnogram duration:", annotation_end / 3600, "hours")
    print("Difference (hypnogram - PSG):",
          annotation_end - psg_duration,
          "seconds")

print()
print("=" * 80)
print("INSPECTION COMPLETE")
print("=" * 80)