import os
import csv
from collections import Counter, defaultdict

import mne


DATASET_ROOT = (
    r"S:\Symbiont\Datasets\raw\sleep-edfx-1.0.0"
    r"\sleep-edf-database-expanded-1.0.0"
)

OUTPUT_DIR = r"S:\Symbiont\research\reconnaissance\outputs"

RECORD_OUTPUT = os.path.join(
    OUTPUT_DIR,
    "dataset_stage_epoch_analysis.csv"
)

STAGE_OUTPUT = os.path.join(
    OUTPUT_DIR,
    "dataset_stage_duration_analysis.csv"
)


def find_hypnogram(subset_path, base):
    """
    Find the hypnogram corresponding to a PSG record.

    The cassette and telemetry naming conventions differ,
    so the matching is based on the shared record prefix.
    """
    prefix = base[:-1]

    candidates = [
        filename
        for filename in os.listdir(subset_path)
        if filename.startswith(prefix)
        and filename.endswith("-Hypnogram.edf")
    ]

    if len(candidates) == 1:
        return candidates[0]

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
            if not filename.endswith("-PSG.edf"):
                continue

            base = filename[:-8]

            hypnogram = find_hypnogram(
                subset_path,
                base
            )

            pairs.append(
                {
                    "subset": subset,
                    "record": base,
                    "psg": os.path.join(
                        subset_path,
                        filename
                    ),
                    "hypnogram": (
                        os.path.join(
                            subset_path,
                            hypnogram
                        )
                        if hypnogram
                        else None
                    ),
                }
            )

    return pairs


def inspect_pair(pair):
    result = {
        "subset": pair["subset"],
        "record": pair["record"],
        "status": "OK",
        "psg_duration_sec": "",
        "hypnogram_duration_sec": "",
        "annotation_count": "",
        "usable_30sec_epoch_count": "",
        "usable_30sec_sleep_epoch_count": "",
        "usable_30sec_wake_epoch_count": "",
        "usable_30sec_movement_epoch_count": "",
        "usable_30sec_unknown_epoch_count": "",
    }

    stage_counts = Counter()
    stage_durations = defaultdict(float)

    try:
        if not pair["hypnogram"]:
            result["status"] = "MISSING_HYPNOGRAM"
            return result, stage_counts, stage_durations

        raw = mne.io.read_raw_edf(
            pair["psg"],
            preload=False,
            verbose=False
        )

        annotations = mne.read_annotations(
            pair["hypnogram"]
        )

        # IMPORTANT:
        # raw.times[-1] is the timestamp of the final sample.
        # The actual recording boundary is one sample interval
        # beyond that timestamp.
        psg_end = (
            raw.times[-1]
            + (1 / raw.info["sfreq"])
        )

        hypnogram_end = 0.0

        sorted_annotations = sorted(
            zip(
                annotations.onset,
                annotations.duration,
                annotations.description
            ),
            key=lambda x: x[0]
        )

        result["psg_duration_sec"] = round(
            psg_end,
            2
        )

        result["annotation_count"] = len(
            sorted_annotations
        )

        usable_30sec = 0
        usable_sleep = 0
        usable_wake = 0
        usable_movement = 0
        usable_unknown = 0

        for onset, duration, description in sorted_annotations:

            end = onset + duration

            if end > hypnogram_end:
                hypnogram_end = end

            # Preserve raw stage counts and durations.
            stage_counts[description] += 1
            stage_durations[description] += duration

            # Only annotations fully contained inside
            # the actual PSG recording are eligible.
            fully_inside_psg = (
                onset >= 0
                and end <= psg_end
            )

            is_30sec = abs(
                duration - 30.0
            ) < 1e-6

            if fully_inside_psg and is_30sec:
                usable_30sec += 1

                if description == "Sleep stage W":
                    usable_wake += 1

                elif description in {
                    "Sleep stage 1",
                    "Sleep stage 2",
                    "Sleep stage 3",
                    "Sleep stage 4",
                    "Sleep stage R",
                }:
                    usable_sleep += 1

                elif description == "Movement time":
                    usable_movement += 1

                elif description == "Sleep stage ?":
                    usable_unknown += 1

        result["hypnogram_duration_sec"] = round(
            hypnogram_end,
            2
        )

        result["usable_30sec_epoch_count"] = (
            usable_30sec
        )

        result["usable_30sec_sleep_epoch_count"] = (
            usable_sleep
        )

        result["usable_30sec_wake_epoch_count"] = (
            usable_wake
        )

        result["usable_30sec_movement_epoch_count"] = (
            usable_movement
        )

        result["usable_30sec_unknown_epoch_count"] = (
            usable_unknown
        )

        return result, stage_counts, stage_durations

    except Exception as exc:
        result["status"] = f"ERROR: {type(exc).__name__}: {exc}"
        return result, stage_counts, stage_durations


def main():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    pairs = find_pairs()

    record_results = []
    stage_results = []

    total = len(pairs)

    for index, pair in enumerate(pairs, start=1):

        print(
            f"[{index}/{total}] "
            f"{pair['subset']} / {pair['record']}"
        )

        result, stage_counts, stage_durations = (
            inspect_pair(pair)
        )

        record_results.append(result)

        for stage in sorted(stage_counts):

            stage_results.append(
                {
                    "subset": pair["subset"],
                    "record": pair["record"],
                    "stage": stage,
                    "annotation_count": stage_counts[stage],
                    "duration_sec": round(
                        stage_durations[stage],
                        2
                    ),
                    "duration_hours": round(
                        stage_durations[stage] / 3600,
                        4
                    ),
                    "exact_30sec_count": sum(
                        1
                        for onset, duration, description
                        in sorted(
                            zip(
                                mne.read_annotations(
                                    pair["hypnogram"]
                                ).onset,
                                mne.read_annotations(
                                    pair["hypnogram"]
                                ).duration,
                                mne.read_annotations(
                                    pair["hypnogram"]
                                ).description
                            ),
                            key=lambda x: x[0]
                        )
                        if description == stage
                        and abs(duration - 30.0) < 1e-6
                    ),
                }
            )

    # Write record-level results.
    record_fields = [
        "subset",
        "record",
        "status",
        "psg_duration_sec",
        "hypnogram_duration_sec",
        "annotation_count",
        "usable_30sec_epoch_count",
        "usable_30sec_sleep_epoch_count",
        "usable_30sec_wake_epoch_count",
        "usable_30sec_movement_epoch_count",
        "usable_30sec_unknown_epoch_count",
    ]

    with open(
        RECORD_OUTPUT,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=record_fields
        )

        writer.writeheader()
        writer.writerows(record_results)

    # Write stage-level results.
    stage_fields = [
        "subset",
        "record",
        "stage",
        "annotation_count",
        "duration_sec",
        "duration_hours",
        "exact_30sec_count",
    ]

    with open(
        STAGE_OUTPUT,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=stage_fields
        )

        writer.writeheader()
        writer.writerows(stage_results)

    # Summary.
    status_counts = Counter(
        row["status"]
        for row in record_results
    )

    total_usable = sum(
        int(row["usable_30sec_epoch_count"])
        for row in record_results
        if row["usable_30sec_epoch_count"] != ""
    )

    total_stage_exact = sum(
        int(row["exact_30sec_count"])
        for row in stage_results
    )

    print()
    print("=" * 60)
    print("PASS 2B SUMMARY")
    print("=" * 60)

    print(f"Records: {total}")
    print("Status:")

    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    print()
    print(
        "Usable exact 30-second epochs "
        f"inside PSG: {total_usable}"
    )

    print(
        "Exact 30-second annotations across "
        f"stage analysis: {total_stage_exact}"
    )

    print()
    print("Record output:")
    print(RECORD_OUTPUT)

    print()
    print("Stage output:")
    print(STAGE_OUTPUT)


if __name__ == "__main__":
    main()