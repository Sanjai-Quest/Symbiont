import os
import csv
from collections import Counter

import mne


DATASET_ROOT = (
    r"S:\Symbiont\Datasets\raw\sleep-edfx-1.0.0"
    r"\sleep-edf-database-expanded-1.0.0"
)

OUTPUT_DIR = r"S:\Symbiont\research\reconnaissance\outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def find_hypnogram(subset_path, base):
    """
    Find the hypnogram corresponding to a PSG file.

    Sleep-EDF uses different suffixes for PSG and hypnogram
    files, so we match using the shared record prefix.
    """

    prefix = base[:-1]

    candidates = []

    for filename in os.listdir(subset_path):

        if (
            filename.startswith(prefix)
            and filename.endswith("-Hypnogram.edf")
        ):
            candidates.append(filename)

    if len(candidates) == 1:
        return os.path.join(
            subset_path,
            candidates[0]
        )

    if len(candidates) == 0:
        return None

    raise RuntimeError(
        f"Multiple hypnograms found for {base}: {candidates}"
    )


def find_pairs():

    pairs = []

    for subset in [
        "sleep-cassette",
        "sleep-telemetry"
    ]:

        subset_path = os.path.join(
            DATASET_ROOT,
            subset
        )

        for filename in os.listdir(subset_path):

            if filename.endswith("-PSG.edf"):

                psg_path = os.path.join(
                    subset_path,
                    filename
                )

                base = filename.replace(
                    "-PSG.edf",
                    ""
                )

                hypnogram_path = find_hypnogram(
                    subset_path,
                    base
                )

                pairs.append({
                    "subset": subset,
                    "record": base,
                    "psg": psg_path,
                    "hypnogram": hypnogram_path
                })

    return sorted(
        pairs,
        key=lambda x: x["record"]
    )


def inspect_pair(pair):

    result = {
        "subset": pair["subset"],
        "record": pair["record"],
        "psg_exists": os.path.exists(pair["psg"]),
        "hypnogram_exists": (
            pair["hypnogram"] is not None
            and os.path.exists(pair["hypnogram"])
        ),
        "psg_channels": "",
        "channel_count": "",
        "sampling_rates": "",
        "psg_duration_hours": "",
        "annotation_count": "",
        "annotation_duration_hours": "",
        "sleep_stages": "",
        "status": "OK",
        "error": ""
    }

    try:

        raw = mne.io.read_raw_edf(
            pair["psg"],
            preload=False,
            verbose=False
        )

        result["channel_count"] = len(
            raw.ch_names
        )

        result["psg_channels"] = " | ".join(
            raw.ch_names
        )

        result["sampling_rates"] = str(
            raw.info["sfreq"]
        )

        result["psg_duration_hours"] = round(
            raw.times[-1] / 3600,
            4
        )

        if not result["hypnogram_exists"]:

            result["status"] = "MISSING_HYPNOGRAM"

            return result

        annotations = mne.read_annotations(
            pair["hypnogram"]
        )

        result["annotation_count"] = len(
            annotations
        )

        if len(annotations) > 0:

            annotation_end = (
                annotations.onset[-1]
                + annotations.duration[-1]
            )

            result["annotation_duration_hours"] = round(
                annotation_end / 3600,
                4
            )

            stages = sorted(
                set(annotations.description)
            )

            result["sleep_stages"] = " | ".join(
                stages
            )

        else:

            result["status"] = "NO_ANNOTATIONS"

    except Exception as e:

        result["status"] = "ERROR"
        result["error"] = repr(e)

    return result


def main():

    print("=" * 70)
    print("SYMBIONT - SLEEP-EDF DATASET RECONNAISSANCE")
    print("=" * 70)

    pairs = find_pairs()

    print(
        f"\nPSG/Hypnogram pairs found: {len(pairs)}"
    )

    results = []

    for index, pair in enumerate(
        pairs,
        start=1
    ):

        print(
            f"[{index}/{len(pairs)}] "
            f"{pair['subset']} / "
            f"{pair['record']}"
        )

        result = inspect_pair(pair)

        results.append(result)

    output_csv = os.path.join(
        OUTPUT_DIR,
        "dataset_reconnaissance.csv"
    )

    fieldnames = results[0].keys()

    with open(
        output_csv,
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

    print("\n" + "=" * 70)
    print("RECONNAISSANCE SUMMARY")
    print("=" * 70)

    status_counts = Counter(
        r["status"]
        for r in results
    )

    print("\nStatus:")

    for status, count in status_counts.items():
        print(
            f"  {status}: {count}"
        )

    channel_counts = Counter(
        r["channel_count"]
        for r in results
        if r["channel_count"] != ""
    )

    print("\nChannel counts:")

    for channels, count in sorted(
        channel_counts.items(),
        key=lambda x: str(x[0])
    ):

        print(
            f"  {channels}: {count}"
        )

    sampling_counts = Counter()

    for r in results:

        if r["sampling_rates"]:
            sampling_counts[
                r["sampling_rates"]
            ] += 1

    print("\nSampling-rate configurations:")

    for rates, count in sampling_counts.items():

        print(
            f"  {rates}: {count}"
        )

    stage_counts = Counter()

    for r in results:

        if r["sleep_stages"]:

            for stage in r[
                "sleep_stages"
            ].split(" | "):

                stage_counts[stage] += 1

    print("\nSleep stages encountered:")

    for stage, count in sorted(
        stage_counts.items()
    ):

        print(
            f"  {stage}: {count}"
        )

    print("\nResults saved to:")
    print(output_csv)


if __name__ == "__main__":
    main()