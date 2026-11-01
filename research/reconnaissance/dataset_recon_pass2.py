import os
import csv
from collections import Counter, defaultdict

import mne


# ============================================================
# SYMBIONT
# Dataset Reconnaissance Pass 2
# PSG ↔ Hypnogram Alignment and Annotation Analysis
# ============================================================

DATASET_ROOT = (
    r"S:\Symbiont\Datasets\raw\sleep-edfx-1.0.0"
    r"\sleep-edf-database-expanded-1.0.0"
)

OUTPUT_DIR = r"S:\Symbiont\research\reconnaissance\outputs"

ALIGNMENT_OUTPUT = os.path.join(
    OUTPUT_DIR,
    "dataset_alignment.csv"
)

STAGE_SUMMARY_OUTPUT = os.path.join(
    OUTPUT_DIR,
    "dataset_stage_summary.csv"
)


# ------------------------------------------------------------
# Find the corresponding hypnogram
# ------------------------------------------------------------

def find_hypnogram(subset_path, base):
    """
    Find the hypnogram associated with a PSG file.

    Sleep-EDF uses different filename patterns between
    subsets, so the relationship is discovered from the
    shared filename prefix rather than hardcoded.
    """

    prefix = base[:-1]

    candidates = [
        name
        for name in os.listdir(subset_path)
        if name.startswith(prefix)
        and name.endswith("-Hypnogram.edf")
    ]

    if len(candidates) == 0:
        return None

    if len(candidates) > 1:
        raise RuntimeError(
            f"Multiple hypnograms found for {base}: {candidates}"
        )

    return os.path.join(subset_path, candidates[0])


# ------------------------------------------------------------
# Find all PSG files
# ------------------------------------------------------------

def find_pairs():
    pairs = []

    for subset in ["sleep-cassette", "sleep-telemetry"]:

        subset_path = os.path.join(
            DATASET_ROOT,
            subset
        )

        for name in sorted(os.listdir(subset_path)):

            if not name.endswith("-PSG.edf"):
                continue

            psg_path = os.path.join(
                subset_path,
                name
            )

            base = name[:-len("-PSG.edf")]

            hypnogram_path = find_hypnogram(
                subset_path,
                base
            )

            pairs.append(
                {
                    "subset": subset,
                    "record": base,
                    "psg_path": psg_path,
                    "hypnogram_path": hypnogram_path
                }
            )

    return pairs


# ------------------------------------------------------------
# Analyse one PSG / hypnogram pair
# ------------------------------------------------------------

def analyse_pair(pair):

    result = {
        "subset": pair["subset"],
        "record": pair["record"],
        "status": "ERROR",

        "psg_duration_sec": "",
        "hypnogram_duration_sec": "",
        "duration_difference_sec": "",

        "annotation_count": "",
        "epoch_30sec_count": "",

        "annotation_gap_count": "",
        "annotation_overlap_count": "",

        "annotation_beyond_psg_count": "",
        "annotation_beyond_psg_duration_sec": ""
    }

    if pair["hypnogram_path"] is None:

        result["status"] = "MISSING_HYPNOGRAM"

        return result, []

    try:

        # ----------------------------------------------------
        # Read PSG
        # ----------------------------------------------------

        raw = mne.io.read_raw_edf(
            pair["psg_path"],
            preload=False,
            verbose=False
        )

        psg_duration = raw.times[-1]

        # ----------------------------------------------------
        # Read hypnogram
        # ----------------------------------------------------

        annotations = mne.read_annotations(
            pair["hypnogram_path"]
        )

        annotation_count = len(annotations)

        if annotation_count == 0:

            result["status"] = "NO_ANNOTATIONS"

            return result, []

        # ----------------------------------------------------
        # Convert annotations into explicit tuples
        # ----------------------------------------------------

        sorted_annotations = sorted(
            zip(
                annotations.onset,
                annotations.duration,
                annotations.description
            ),
            key=lambda x: x[0]
        )

        # ----------------------------------------------------
        # Determine annotation coverage
        # ----------------------------------------------------

        annotation_end_times = (
            annotations.onset + annotations.duration
        )

        hypnogram_duration = max(
            annotation_end_times
        )

        duration_difference = (
            hypnogram_duration - psg_duration
        )

        # ----------------------------------------------------
        # 30-second epoch analysis
        # ----------------------------------------------------

        epoch_30sec_count = sum(
            1
            for onset, duration, description
            in sorted_annotations
            if abs(duration - 30.0) < 0.001
        )

        # ----------------------------------------------------
        # Gap / overlap analysis
        # ----------------------------------------------------

        gap_count = 0
        overlap_count = 0

        previous_end = None

        for onset, duration, description in sorted_annotations:

            end = onset + duration

            if previous_end is not None:

                difference = onset - previous_end

                if difference > 0.001:

                    gap_count += 1

                elif difference < -0.001:

                    overlap_count += 1

            if previous_end is None:
                previous_end = end
            else:
                previous_end = max(
                    previous_end,
                    end
                )

        # ----------------------------------------------------
        # Annotations extending beyond PSG
        # ----------------------------------------------------

        beyond_count = 0
        beyond_duration = 0.0

        for onset, duration, description in sorted_annotations:

            end = onset + duration

            if onset >= psg_duration:

                beyond_count += 1

                beyond_duration += duration

            elif end > psg_duration:

                beyond_count += 1

                beyond_duration += (
                    end - psg_duration
                )

        # ----------------------------------------------------
        # Store alignment results
        # ----------------------------------------------------

        result["status"] = "OK"

        result["psg_duration_sec"] = round(
            psg_duration,
            3
        )

        result["hypnogram_duration_sec"] = round(
            hypnogram_duration,
            3
        )

        result["duration_difference_sec"] = round(
            duration_difference,
            3
        )

        result["annotation_count"] = (
            annotation_count
        )

        result["epoch_30sec_count"] = (
            epoch_30sec_count
        )

        result["annotation_gap_count"] = (
            gap_count
        )

        result["annotation_overlap_count"] = (
            overlap_count
        )

        result["annotation_beyond_psg_count"] = (
            beyond_count
        )

        result["annotation_beyond_psg_duration_sec"] = round(
            beyond_duration,
            3
        )

        # ----------------------------------------------------
        # Stage duration analysis
        # ----------------------------------------------------

        stage_durations = defaultdict(float)

        for onset, duration, description in sorted_annotations:

            stage_durations[description] += duration

        stage_rows = []

        for stage, duration in sorted(
            stage_durations.items()
        ):

            stage_rows.append(
                {
                    "subset": pair["subset"],
                    "record": pair["record"],
                    "stage": stage,
                    "duration_sec": round(
                        duration,
                        3
                    ),
                    "duration_hours": round(
                        duration / 3600,
                        4
                    )
                }
            )

        return result, stage_rows

    except Exception as exc:

        result["status"] = (
            f"ERROR: {type(exc).__name__}: {exc}"
        )

        return result, []


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    pairs = find_pairs()

    alignment_rows = []
    stage_rows = []

    print("=" * 70)
    print("SYMBIONT - RECONNAISSANCE PASS 2")
    print("PSG / HYPNOGRAM ALIGNMENT ANALYSIS")
    print("=" * 70)

    print()
    print(
        f"Records discovered: {len(pairs)}"
    )
    print()

    for index, pair in enumerate(
        pairs,
        start=1
    ):

        print(
            f"[{index}/{len(pairs)}] "
            f"{pair['subset']} / "
            f"{pair['record']}"
        )

        result, stages = analyse_pair(
            pair
        )

        alignment_rows.append(
            result
        )

        stage_rows.extend(
            stages
        )

    # --------------------------------------------------------
    # Write alignment CSV
    # --------------------------------------------------------

    alignment_fields = [
        "subset",
        "record",
        "status",
        "psg_duration_sec",
        "hypnogram_duration_sec",
        "duration_difference_sec",
        "annotation_count",
        "epoch_30sec_count",
        "annotation_gap_count",
        "annotation_overlap_count",
        "annotation_beyond_psg_count",
        "annotation_beyond_psg_duration_sec"
    ]

    with open(
        ALIGNMENT_OUTPUT,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=alignment_fields
        )

        writer.writeheader()

        writer.writerows(
            alignment_rows
        )

    # --------------------------------------------------------
    # Write stage summary CSV
    # --------------------------------------------------------

    stage_fields = [
        "subset",
        "record",
        "stage",
        "duration_sec",
        "duration_hours"
    ]

    with open(
        STAGE_SUMMARY_OUTPUT,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=stage_fields
        )

        writer.writeheader()

        writer.writerows(
            stage_rows
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    status_counts = Counter(
        row["status"]
        for row in alignment_rows
    )

    print()
    print("=" * 70)
    print("PASS 2 SUMMARY")
    print("=" * 70)

    print()
    print("Status:")

    for status, count in sorted(
        status_counts.items()
    ):

        print(
            f"  {status}: {count}"
        )

    print()
    print("Outputs:")

    print(
        f"  {ALIGNMENT_OUTPUT}"
    )

    print(
        f"  {STAGE_SUMMARY_OUTPUT}"
    )

    print()
    print(
        "Pass 2 analysis complete."
    )


if __name__ == "__main__":
    main()