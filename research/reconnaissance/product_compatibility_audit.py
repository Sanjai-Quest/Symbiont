import os
import csv
from collections import Counter, defaultdict

import mne


DATASET_ROOT = r"S:\Symbiont\Datasets\raw\sleep-edfx-1.0.0\sleep-edf-database-expanded-1.0.0"
OUTPUT_DIR = r"S:\Symbiont\research\reconnaissance\outputs"


def find_hypnogram(subset_path, base):
    prefix = base[:-1]

    candidates = [
        filename
        for filename in os.listdir(subset_path)
        if filename.startswith(prefix)
        and filename.endswith("-Hypnogram.edf")
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
        subset_path = os.path.join(DATASET_ROOT, subset)

        for filename in sorted(os.listdir(subset_path)):
            if filename.endswith("-PSG.edf"):

                base = filename[:-8]

                psg_path = os.path.join(
                    subset_path,
                    filename
                )

                hypnogram_path = find_hypnogram(
                    subset_path,
                    base
                )

                pairs.append({
                    "subset": subset,
                    "record": base,
                    "psg_path": psg_path,
                    "hypnogram_path": hypnogram_path,
                })

    return pairs


def inspect_annotations(file_path):
    """
    Read annotations from one EDF file and return
    the annotation descriptions, counts and durations.
    """

    annotations = mne.read_annotations(file_path)

    descriptions = Counter()
    durations = defaultdict(list)

    for description, duration in zip(
        annotations.description,
        annotations.duration
    ):
        descriptions[description] += 1
        durations[description].append(float(duration))

    return annotations, descriptions, durations


def inspect_psg(pair):

    result = {
        "subset": pair["subset"],
        "record": pair["record"],
        "file_type": "PSG",
        "status": "OK",
        "channel_count": 0,
        "channels": "",
        "annotation_count": 0,
        "annotation_types": "",
        "error": "",
    }

    try:

        raw = mne.io.read_raw_edf(
            pair["psg_path"],
            preload=False,
            verbose=False
        )

        result["channel_count"] = len(raw.ch_names)
        result["channels"] = " | ".join(raw.ch_names)

        annotations, descriptions, durations = inspect_annotations(
            pair["psg_path"]
        )

        result["annotation_count"] = len(annotations)

        result["annotation_types"] = " | ".join(
            sorted(descriptions.keys())
        )

    except Exception as exc:

        result["status"] = "ERROR"
        result["error"] = repr(exc)

    return result


def inspect_hypnogram(pair):

    result = {
        "subset": pair["subset"],
        "record": pair["record"],
        "file_type": "Hypnogram",
        "status": "OK",
        "channel_count": 0,
        "channels": "",
        "annotation_count": 0,
        "annotation_types": "",
        "error": "",
    }

    if pair["hypnogram_path"] is None:

        result["status"] = "MISSING_HYPNOGRAM"

        return result

    try:

        raw = mne.io.read_raw_edf(
            pair["hypnogram_path"],
            preload=False,
            verbose=False
        )

        result["channel_count"] = len(raw.ch_names)
        result["channels"] = " | ".join(raw.ch_names)

        annotations, descriptions, durations = inspect_annotations(
            pair["hypnogram_path"]
        )

        result["annotation_count"] = len(annotations)

        result["annotation_types"] = " | ".join(
            sorted(descriptions.keys())
        )

    except Exception as exc:

        result["status"] = "ERROR"
        result["error"] = repr(exc)

    return result


def main():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    pairs = find_pairs()

    print("=" * 70)
    print("SYMBIONT PRODUCT COMPATIBILITY AUDIT")
    print("=" * 70)

    print(
        f"Records discovered: {len(pairs)}"
    )

    print()

    results = []

    for index, pair in enumerate(
        pairs,
        start=1
    ):

        print(
            f"Processing {index}/{len(pairs)}: "
            f"{pair['record']}"
        )

        results.append(
            inspect_psg(pair)
        )

        results.append(
            inspect_hypnogram(pair)
        )

    output_file = os.path.join(
        OUTPUT_DIR,
        "product_compatibility_annotation_inventory.csv"
    )

    fieldnames = [
        "subset",
        "record",
        "file_type",
        "status",
        "channel_count",
        "channels",
        "annotation_count",
        "annotation_types",
        "error",
    ]

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(results)

    print()
    print("=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)

    print(
        f"Results saved to:\n{output_file}"
    )


if __name__ == "__main__":
    main()