from pathlib import Path

import h5py
import numpy as np
import wfdb


ROOT = Path("Datasets/raw/physionet-challenge-2018/training")


def validate_record(record_dir: Path) -> bool:
    record_id = record_dir.name
    base = record_dir / record_id

    signal_base = str(base)
    arousal_mat = record_dir / f"{record_id}-arousal.mat"

    print("=" * 70)
    print(record_id)

    # -----------------------------
    # PSG signal
    # -----------------------------
    record = wfdb.rdrecord(signal_base)

    signal_samples = record.p_signal.shape[0]
    channel_count = len(record.sig_name)
    sampling_rate = record.fs

    print(f"  SIGNAL SAMPLES : {signal_samples:,}")
    print(f"  SAMPLING RATE  : {sampling_rate} Hz")
    print(f"  CHANNELS       : {channel_count}")
    print(f"  CHANNEL NAMES  : {record.sig_name}")

    # -----------------------------
    # Arousal target
    # -----------------------------
    with h5py.File(arousal_mat, "r") as f:
        arousals = np.asarray(
            f["data"]["arousals"]
        ).ravel()

        stage_group = f["data"]["sleep_stages"]

        stage_lengths = {
            name: stage_group[name].shape[-1]
            for name in stage_group.keys()
        }

    arousal_length = len(arousals)

    values, counts = np.unique(
        arousals,
        return_counts=True,
    )

    distribution = {
        float(value): int(count)
        for value, count in zip(values, counts)
    }

    print(f"  AROUSAL SAMPLES: {arousal_length:,}")
    print(f"  AROUSAL VALUES : {distribution}")

    # -----------------------------
    # Sleep stages
    # -----------------------------
    print("  SLEEP STAGES:")

    for name, length in stage_lengths.items():
        print(f"    {name}: {length:,}")

    # -----------------------------
    # Validation
    # -----------------------------
    valid_values = set(distribution.keys()) <= {
        -1.0,
        0.0,
        1.0,
    }

    length_match = (
        signal_samples == arousal_length
        and all(
            length == signal_samples
            for length in stage_lengths.values()
        )
    )

    passed = (
        sampling_rate == 200
        and length_match
        and valid_values
    )

    print(f"  LENGTH MATCH   : {length_match}")
    print(f"  VALID LABELS   : {valid_values}")
    print(f"  RESULT         : {'PASS' if passed else 'FAIL'}")

    return passed


def main():
    record_dirs = sorted(
        p.parent
        for p in ROOT.glob("*/*/*-arousal.mat")
    )

    print(f"Development records found: {len(record_dirs)}")
    print()

    results = []

    for record_dir in record_dirs:
        try:
            passed = validate_record(record_dir)
        except Exception as exc:
            print(f"  RESULT         : ERROR")
            print(f"  ERROR          : {exc}")
            passed = False

        results.append(
            (record_dir.name, passed)
        )

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for record_id, passed in results:
        print(
            f"{record_id}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    passed_count = sum(
        passed for _, passed in results
    )

    print()
    print(
        f"TOTAL: {passed_count}/{len(results)} PASS"
    )


if __name__ == "__main__":
    main()