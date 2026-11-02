import os
import csv
from collections import Counter

import mne


DATASET_ROOT = r"S:\Symbiont\Datasets\raw\sleep-edfx-1.0.0\sleep-edf-database-expanded-1.0.0"
OUTPUT_DIR = r"S:\Symbiont\research\reconnaissance\outputs"


def find_hypnogram(subset_path, base):
    """
    Find the hypnogram associated with a PSG using the shared record prefix.
    """
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
    """
    Find all PSG files and their corresponding hypnograms.
    """
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
    """
    Inspect one PSG/hypnogram pair.
    """

    result = {
        "subset": pair["subset"],
        "record": pair["record"],
        "status": "OK",
        "psg_duration_sec": "",
        "sampling_rate": "",
        "channel_count": "",
        "channel_names": "",
        "channel_types": "",
        "has_eeg": False,
        "has_eog": False,
        "has_emg": False,
        "has_respiration": False,
        "has_temperature": False,
        "has_event_marker": False,
        "hypnogram_present": False,
        "annotation_count": 0,
        "usable_annotation_count": 0,
        "usable_sleep_epoch_count": 0,
        "usable_wake_epoch_count": 0,
        "usable_movement_epoch_count": 0,
        "usable_unknown_epoch_count": 0,
        "stage_W_epochs": 0,
        "stage_1_epochs": 0,
        "stage_2_epochs": 0,
        "stage_3_epochs": 0,
        "stage_4_epochs": 0,
        "stage_R_epochs": 0,
        "stage_Movement_epochs": 0,
        "stage_Unknown_epochs": 0,
        "error": "",
    }

    try:
        # ------------------------------------------------------------
        # Read PSG
        # ------------------------------------------------------------

        raw = mne.io.read_raw_edf(
            pair["psg_path"],
            preload=False,
            verbose=False
        )

        # The actual recording boundary is one sample interval
        # after the timestamp of the final sample.
        psg_end = raw.times[-1] + (1 / raw.info["sfreq"])

        result["psg_duration_sec"] = round(
            psg_end,
            2
        )

        result["sampling_rate"] = raw.info["sfreq"]

        result["channel_count"] = len(raw.ch_names)

        result["channel_names"] = " | ".join(
            raw.ch_names
        )

        # Keep MNE's reported channel types for reference,
        # but do NOT use them as the authoritative modality
        # classification for this dataset.
        channel_types = raw.get_channel_types()

        result["channel_types"] = " | ".join(
            channel_types
        )

        # ------------------------------------------------------------
        # Channel capability detection
        #
        # IMPORTANT:
        # Sleep-EDF EDF channel metadata may cause MNE to classify
        # several physiological channels as "eeg".
        #
        # Therefore, modality detection is based on the actual
        # EDF channel names.
        # ------------------------------------------------------------

        for name in raw.ch_names:

            name_lower = name.lower().strip()

            # EEG
            if name_lower.startswith("eeg "):
                result["has_eeg"] = True

            # EOG
            if "eog" in name_lower:
                result["has_eog"] = True

            # EMG
            if "emg" in name_lower:
                result["has_emg"] = True

            # Respiration
            if (
                "resp" in name_lower
                or "oro" in name_lower
                or "airflow" in name_lower
            ):
                result["has_respiration"] = True

            # Temperature
            if (
                "temp" in name_lower
                or "temperature" in name_lower
            ):
                result["has_temperature"] = True

            # Event / marker
            if (
                "event" in name_lower
                or "marker" in name_lower
            ):
                result["has_event_marker"] = True

        # ------------------------------------------------------------
        # Hypnogram
        # ------------------------------------------------------------

        if pair["hypnogram_path"] is None:

            result["status"] = "MISSING_HYPNOGRAM"

            return result

        result["hypnogram_present"] = True

        annotations = mne.read_annotations(
            pair["hypnogram_path"]
        )

        result["annotation_count"] = len(
            annotations
        )

        # Sort annotations chronologically.
        sorted_annotations = sorted(
            zip(
                annotations.onset,
                annotations.duration,
                annotations.description
            ),
            key=lambda x: x[0]
        )

        # ------------------------------------------------------------
        # Exact 30-second epoch analysis
        # ------------------------------------------------------------

        for onset, duration, description in sorted_annotations:

            annotation_end = onset + duration

            # Only count exact 30-second annotations that are
            # completely contained inside the actual PSG.
            if (
                abs(duration - 30.0) < 1e-6
                and onset >= 0
                and annotation_end <= psg_end + 1e-6
            ):

                result["usable_annotation_count"] += 1

                # Wake
                if description == "Sleep stage W":

                    result["stage_W_epochs"] += 1

                    result["usable_wake_epoch_count"] += 1

                # Stage 1
                elif description == "Sleep stage 1":

                    result["stage_1_epochs"] += 1

                    result["usable_sleep_epoch_count"] += 1

                # Stage 2
                elif description == "Sleep stage 2":

                    result["stage_2_epochs"] += 1

                    result["usable_sleep_epoch_count"] += 1

                # Stage 3
                elif description == "Sleep stage 3":

                    result["stage_3_epochs"] += 1

                    result["usable_sleep_epoch_count"] += 1

                # Stage 4
                elif description == "Sleep stage 4":

                    result["stage_4_epochs"] += 1

                    result["usable_sleep_epoch_count"] += 1

                # REM
                elif description == "Sleep stage R":

                    result["stage_R_epochs"] += 1

                    result["usable_sleep_epoch_count"] += 1

                # Movement
                elif description == "Movement time":

                    result["stage_Movement_epochs"] += 1

                    result["usable_movement_epoch_count"] += 1

                # Unknown
                elif description == "Sleep stage ?":

                    result["stage_Unknown_epochs"] += 1

                    result["usable_unknown_epoch_count"] += 1

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
    print("SYMBIONT DATASET CAPABILITY AUDIT")
    print("=" * 70)

    print(
        f"Records discovered: {len(pairs)}"
    )

    print()

    results = []

    # ------------------------------------------------------------
    # Process all records
    # ------------------------------------------------------------

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

    # ------------------------------------------------------------
    # Save CSV
    # ------------------------------------------------------------

    output_csv = os.path.join(
        OUTPUT_DIR,
        "dataset_capability_audit.csv"
    )

    fieldnames = list(
        results[0].keys()
    )

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

    # ------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------

    print()

    print("=" * 70)
    print("AUDIT SUMMARY")
    print("=" * 70)

    # Status
    status_counts = Counter(
        r["status"]
        for r in results
    )

    print()
    print("Status:")

    for status, count in sorted(
        status_counts.items()
    ):

        print(
            f"  {status}: {count}"
        )

    # Channel counts
    print()
    print("Channel counts:")

    channel_counts = Counter(
        r["channel_count"]
        for r in results
        if r["status"] == "OK"
    )

    for count, number in sorted(
        channel_counts.items()
    ):

        print(
            f"  {count}: {number}"
        )

    # Sampling rates
    print()
    print("Sampling rates:")

    sampling_counts = Counter(
        r["sampling_rate"]
        for r in results
        if r["status"] == "OK"
    )

    for rate, number in sorted(
        sampling_counts.items()
    ):

        print(
            f"  {rate} Hz: {number}"
        )

    # Signal capabilities
    print()
    print("Signal capabilities:")

    capability_fields = [
        ("EEG", "has_eeg"),
        ("EOG", "has_eog"),
        ("EMG", "has_emg"),
        ("Respiration", "has_respiration"),
        ("Temperature", "has_temperature"),
        ("Event marker", "has_event_marker"),
    ]

    for label, field in capability_fields:

        count = sum(
            1
            for r in results
            if (
                r["status"] == "OK"
                and r[field]
            )
        )

        print(
            f"  {label}: {count}/{len(results)}"
        )

    # Epoch counts
    print()
    print(
        "Exact 30-second epochs inside PSG:"
    )

    epoch_fields = [
        ("W", "stage_W_epochs"),
        ("Stage 1", "stage_1_epochs"),
        ("Stage 2", "stage_2_epochs"),
        ("Stage 3", "stage_3_epochs"),
        ("Stage 4", "stage_4_epochs"),
        ("REM", "stage_R_epochs"),
        ("Movement", "stage_Movement_epochs"),
        ("Unknown", "stage_Unknown_epochs"),
    ]

    for label, field in epoch_fields:

        total = sum(
            r[field]
            for r in results
            if r["status"] == "OK"
        )

        records = sum(
            1
            for r in results
            if (
                r["status"] == "OK"
                and r[field] > 0
            )
        )

        print(
            f"  {label:<10}: "
            f"{total:>6} epochs "
            f"across {records:>3} records"
        )

    # Usable totals
    total_usable = sum(
        r["usable_annotation_count"]
        for r in results
        if r["status"] == "OK"
    )

    total_sleep = sum(
        r["usable_sleep_epoch_count"]
        for r in results
        if r["status"] == "OK"
    )

    total_wake = sum(
        r["usable_wake_epoch_count"]
        for r in results
        if r["status"] == "OK"
    )

    print()
    print("Usable-data totals:")

    print(
        f"  All exact 30-sec epochs: "
        f"{total_usable}"
    )

    print(
        f"  Sleep stages 1/2/3/4/R: "
        f"{total_sleep}"
    )

    print(
        f"  Wake: {total_wake}"
    )

    # Unique channel configurations
    print()
    print("Unique channel configurations:")

    configurations = Counter(
        (
            r["channel_names"],
            r["channel_types"]
        )
        for r in results
        if r["status"] == "OK"
    )

    for (
        (names, types),
        count
    ) in configurations.items():

        print()
        print(
            f"  Records: {count}"
        )

        print(
            f"  Channels: {names}"
        )

        print(
            f"  MNE Types: {types}"
        )

    # Output location
    print()
    print("Results saved to:")
    print(output_csv)

    print("=" * 70)


if __name__ == "__main__":
    main()