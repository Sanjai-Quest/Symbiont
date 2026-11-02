import os
import csv
from collections import Counter, defaultdict

import mne


DATASET_ROOT = r"S:\Symbiont\Datasets\raw\sleep-edfx-1.0.0\sleep-edf-database-expanded-1.0.0"
OUTPUT_DIR = r"S:\Symbiont\research\reconnaissance\outputs"


TARGET_STAGES = [
    "Sleep stage W",
    "Sleep stage 1",
    "Sleep stage 2",
    "Sleep stage 3",
    "Sleep stage 4",
    "Sleep stage R",
    "Movement time",
    "Sleep stage ?",
]


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


def inspect_record(pair):

    result = {
        "subset": pair["subset"],
        "record": pair["record"],
        "status": "OK",
        "psg_duration_sec": 0.0,
        "annotation_count": 0,
        "inside_annotation_count": 0,
        "usable_annotated_seconds": 0.0,
        "usable_exact_30sec_epochs": 0,

        "W_seconds": 0.0,
        "Stage1_seconds": 0.0,
        "Stage2_seconds": 0.0,
        "Stage3_seconds": 0.0,
        "Stage4_seconds": 0.0,
        "REM_seconds": 0.0,
        "Movement_seconds": 0.0,
        "Unknown_seconds": 0.0,

        "W_exact_30sec": 0,
        "Stage1_exact_30sec": 0,
        "Stage2_exact_30sec": 0,
        "Stage3_exact_30sec": 0,
        "Stage4_exact_30sec": 0,
        "REM_exact_30sec": 0,
        "Movement_exact_30sec": 0,
        "Unknown_exact_30sec": 0,

        "W_constructible_30sec": 0,
        "Stage1_constructible_30sec": 0,
        "Stage2_constructible_30sec": 0,
        "Stage3_constructible_30sec": 0,
        "Stage4_constructible_30sec": 0,
        "REM_constructible_30sec": 0,
        "Movement_constructible_30sec": 0,
        "Unknown_constructible_30sec": 0,

        "error": "",
    }

    try:

        # ----------------------------------------------------------
        # PSG
        # ----------------------------------------------------------

        raw = mne.io.read_raw_edf(
            pair["psg_path"],
            preload=False,
            verbose=False
        )

        psg_end = raw.times[-1] + (
            1 / raw.info["sfreq"]
        )

        result["psg_duration_sec"] = round(
            psg_end,
            2
        )

        if pair["hypnogram_path"] is None:
            result["status"] = "MISSING_HYPNOGRAM"
            return result

        annotations = mne.read_annotations(
            pair["hypnogram_path"]
        )

        result["annotation_count"] = len(
            annotations
        )

        # ----------------------------------------------------------
        # Sort annotations
        # ----------------------------------------------------------

        sorted_annotations = sorted(
            zip(
                annotations.onset,
                annotations.duration,
                annotations.description
            ),
            key=lambda x: x[0]
        )

        # ----------------------------------------------------------
        # Clip annotation intervals to the PSG boundary
        #
        # This does NOT modify the raw data.
        #
        # It only asks:
        # "How much of each annotation actually overlaps the PSG?"
        # ----------------------------------------------------------

        clipped_intervals = []

        for onset, duration, description in sorted_annotations:

            start = max(
                onset,
                0.0
            )

            end = min(
                onset + duration,
                psg_end
            )

            if end <= start:
                continue

            clipped_duration = end - start

            clipped_intervals.append(
                (
                    start,
                    end,
                    clipped_duration,
                    description
                )
            )

            result["inside_annotation_count"] += 1

            result["usable_annotated_seconds"] += (
                clipped_duration
            )

            # Stage duration accounting
            if description == "Sleep stage W":
                result["W_seconds"] += clipped_duration

            elif description == "Sleep stage 1":
                result["Stage1_seconds"] += clipped_duration

            elif description == "Sleep stage 2":
                result["Stage2_seconds"] += clipped_duration

            elif description == "Sleep stage 3":
                result["Stage3_seconds"] += clipped_duration

            elif description == "Sleep stage 4":
                result["Stage4_seconds"] += clipped_duration

            elif description == "Sleep stage R":
                result["REM_seconds"] += clipped_duration

            elif description == "Movement time":
                result["Movement_seconds"] += clipped_duration

            elif description == "Sleep stage ?":
                result["Unknown_seconds"] += clipped_duration

        # ----------------------------------------------------------
        # Exact 30-second annotations
        # ----------------------------------------------------------

        for start, end, duration, description in clipped_intervals:

            if abs(duration - 30.0) < 1e-6:

                result["usable_exact_30sec_epochs"] += 1

                if description == "Sleep stage W":
                    result["W_exact_30sec"] += 1

                elif description == "Sleep stage 1":
                    result["Stage1_exact_30sec"] += 1

                elif description == "Sleep stage 2":
                    result["Stage2_exact_30sec"] += 1

                elif description == "Sleep stage 3":
                    result["Stage3_exact_30sec"] += 1

                elif description == "Sleep stage 4":
                    result["Stage4_exact_30sec"] += 1

                elif description == "Sleep stage R":
                    result["REM_exact_30sec"] += 1

                elif description == "Movement time":
                    result["Movement_exact_30sec"] += 1

                elif description == "Sleep stage ?":
                    result["Unknown_exact_30sec"] += 1

        # ----------------------------------------------------------
        # Constructible 30-second epochs
        #
        # For each annotation, calculate how many complete
        # 30-second epochs could theoretically be generated from
        # its duration.
        #
        # IMPORTANT:
        # This is an analytical count only.
        # We are NOT creating epochs yet.
        # ----------------------------------------------------------

        for start, end, duration, description in clipped_intervals:

            constructible = int(
                duration // 30.0
            )

            if description == "Sleep stage W":
                result["W_constructible_30sec"] += constructible

            elif description == "Sleep stage 1":
                result["Stage1_constructible_30sec"] += constructible

            elif description == "Sleep stage 2":
                result["Stage2_constructible_30sec"] += constructible

            elif description == "Sleep stage 3":
                result["Stage3_constructible_30sec"] += constructible

            elif description == "Sleep stage 4":
                result["Stage4_constructible_30sec"] += constructible

            elif description == "Sleep stage R":
                result["REM_constructible_30sec"] += constructible

            elif description == "Movement time":
                result["Movement_constructible_30sec"] += constructible

            elif description == "Sleep stage ?":
                result["Unknown_constructible_30sec"] += constructible

        return result

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
    print("SYMBIONT LABEL AND EPOCH AUDIT")
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

        result = inspect_record(pair)

        results.append(result)

        if (
            index % 10 == 0
            or index == len(pairs)
        ):

            print(
                f"Processed: {index}/{len(pairs)}"
            )

    # --------------------------------------------------------------
    # Save record-level results
    # --------------------------------------------------------------

    record_output = os.path.join(
        OUTPUT_DIR,
        "dataset_label_epoch_audit.csv"
    )

    fieldnames = list(
        results[0].keys()
    )

    with open(
        record_output,
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

    # --------------------------------------------------------------
    # Dataset-wide totals
    # --------------------------------------------------------------

    successful = [
        r
        for r in results
        if r["status"] == "OK"
    ]

    print()
    print("=" * 70)
    print("DATASET-WIDE LABEL ANALYSIS")
    print("=" * 70)

    stage_definitions = [
        ("Wake", "W_seconds"),
        ("Stage 1", "Stage1_seconds"),
        ("Stage 2", "Stage2_seconds"),
        ("Stage 3", "Stage3_seconds"),
        ("Stage 4", "Stage4_seconds"),
        ("REM", "REM_seconds"),
        ("Movement", "Movement_seconds"),
        ("Unknown", "Unknown_seconds"),
    ]

    total_seconds = 0.0

    for label, field in stage_definitions:

        total = sum(
            r[field]
            for r in successful
        )

        records = sum(
            1
            for r in successful
            if r[field] > 0
        )

        total_seconds += total

        print(
            f"{label:<12}: "
            f"{total / 3600:>10.2f} hours "
            f"across {records:>3} records"
        )

    print()
    print(
        f"Total annotated time inside PSG: "
        f"{total_seconds / 3600:.2f} hours"
    )

    # --------------------------------------------------------------
    # Exact 30-second totals
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print("EXACT 30-SECOND ANNOTATIONS")
    print("=" * 70)

    exact_fields = [
        ("Wake", "W_exact_30sec"),
        ("Stage 1", "Stage1_exact_30sec"),
        ("Stage 2", "Stage2_exact_30sec"),
        ("Stage 3", "Stage3_exact_30sec"),
        ("Stage 4", "Stage4_exact_30sec"),
        ("REM", "REM_exact_30sec"),
        ("Movement", "Movement_exact_30sec"),
        ("Unknown", "Unknown_exact_30sec"),
    ]

    exact_total = 0

    for label, field in exact_fields:

        total = sum(
            r[field]
            for r in successful
        )

        records = sum(
            1
            for r in successful
            if r[field] > 0
        )

        exact_total += total

        print(
            f"{label:<12}: "
            f"{total:>6} epochs "
            f"across {records:>3} records"
        )

    print()
    print(
        f"Total exact 30-sec annotations: "
        f"{exact_total}"
    )

    # --------------------------------------------------------------
    # Constructible 30-second totals
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print("CONSTRUCTIBLE 30-SECOND EPOCHS")
    print("=" * 70)

    constructible_fields = [
        ("Wake", "W_constructible_30sec"),
        ("Stage 1", "Stage1_constructible_30sec"),
        ("Stage 2", "Stage2_constructible_30sec"),
        ("Stage 3", "Stage3_constructible_30sec"),
        ("Stage 4", "Stage4_constructible_30sec"),
        ("REM", "REM_constructible_30sec"),
        ("Movement", "Movement_constructible_30sec"),
        ("Unknown", "Unknown_constructible_30sec"),
    ]

    constructible_total = 0

    for label, field in constructible_fields:

        total = sum(
            r[field]
            for r in successful
        )

        records = sum(
            1
            for r in successful
            if r[field] > 0
        )

        constructible_total += total

        print(
            f"{label:<12}: "
            f"{total:>6} epochs "
            f"across {records:>3} records"
        )

    print()
    print(
        f"Total constructible 30-sec epochs: "
        f"{constructible_total}"
    )

    # --------------------------------------------------------------
    # Sleep-only usable data
    # --------------------------------------------------------------

    sleep_exact = sum(
        r["Stage1_exact_30sec"]
        + r["Stage2_exact_30sec"]
        + r["Stage3_exact_30sec"]
        + r["Stage4_exact_30sec"]
        + r["REM_exact_30sec"]
        for r in successful
    )

    sleep_constructible = sum(
        r["Stage1_constructible_30sec"]
        + r["Stage2_constructible_30sec"]
        + r["Stage3_constructible_30sec"]
        + r["Stage4_constructible_30sec"]
        + r["REM_constructible_30sec"]
        for r in successful
    )

    wake_exact = sum(
        r["W_exact_30sec"]
        for r in successful
    )

    wake_constructible = sum(
        r["W_constructible_30sec"]
        for r in successful
    )

    print()
    print("=" * 70)
    print("SUPERVISED-DATA CANDIDATE TOTALS")
    print("=" * 70)

    print(
        f"Exact sleep epochs:        {sleep_exact}"
    )

    print(
        f"Constructible sleep epochs:{sleep_constructible}"
    )

    print(
        f"Exact wake epochs:         {wake_exact}"
    )

    print(
        f"Constructible wake epochs: {wake_constructible}"
    )

    print()
    print("Results saved to:")
    print(record_output)

    print("=" * 70)


if __name__ == "__main__":
    main()