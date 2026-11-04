from pathlib import Path

import h5py
import numpy as np
import wfdb


ROOT = Path("Datasets/raw/physionet-challenge-2018/training")


def analyze_record(record_dir: Path):
    record_id = record_dir.name
    base = record_dir / record_id
    arousal_mat = record_dir / f"{record_id}-arousal.mat"

    record = wfdb.rdrecord(str(base))

    total_samples = record.p_signal.shape[0]
    sampling_rate = record.fs
    duration_seconds = total_samples / sampling_rate

    with h5py.File(arousal_mat, "r") as f:
        arousals = np.asarray(
            f["data"]["arousals"]
        ).ravel()

    excluded = np.sum(arousals == -1)
    non_arousal = np.sum(arousals == 0)
    arousal = np.sum(arousals == 1)

    scored = non_arousal + arousal

    print("=" * 70)
    print(record_id)

    print(f"  TOTAL SAMPLES      : {total_samples:,}")
    print(f"  SAMPLING RATE      : {sampling_rate} Hz")
    print(f"  DURATION           : {duration_seconds / 3600:.2f} hours")

    print(f"  SCORED SAMPLES     : {scored:,}")
    print(f"  EXCLUDED (-1)      : {excluded:,}")
    print(f"  NON-AROUSAL (0)    : {non_arousal:,}")
    print(f"  AROUSAL (+1)       : {arousal:,}")

    print()
    print(f"  SCORED %           : {scored / total_samples * 100:.2f}%")
    print(f"  EXCLUDED %         : {excluded / total_samples * 100:.2f}%")
    print(f"  NON-AROUSAL %      : {non_arousal / total_samples * 100:.2f}%")
    print(f"  AROUSAL %          : {arousal / total_samples * 100:.2f}%")

    return {
        "record_id": record_id,
        "total_samples": int(total_samples),
        "sampling_rate": float(sampling_rate),
        "duration_hours": duration_seconds / 3600,
        "scored_samples": int(scored),
        "excluded_samples": int(excluded),
        "non_arousal_samples": int(non_arousal),
        "arousal_samples": int(arousal),
        "scored_pct": scored / total_samples * 100,
        "excluded_pct": excluded / total_samples * 100,
        "non_arousal_pct": non_arousal / total_samples * 100,
        "arousal_pct": arousal / total_samples * 100,
    }


def main():
    record_dirs = sorted(
        p.parent
        for p in ROOT.glob("*/*/*-arousal.mat")
    )

    print(f"Development records found: {len(record_dirs)}")
    print()

    results = []

    for record_dir in record_dirs:
        results.append(
            analyze_record(record_dir)
        )

    print()
    print("=" * 70)
    print("AGGREGATE TOTAL")
    print("=" * 70)

    total_samples = sum(
        r["total_samples"] for r in results
    )

    scored_samples = sum(
        r["scored_samples"] for r in results
    )

    excluded_samples = sum(
        r["excluded_samples"] for r in results
    )

    non_arousal_samples = sum(
        r["non_arousal_samples"] for r in results
    )

    arousal_samples = sum(
        r["arousal_samples"] for r in results
    )

    print(f"  TOTAL SAMPLES      : {total_samples:,}")
    print(f"  SCORED SAMPLES     : {scored_samples:,}")
    print(f"  EXCLUDED SAMPLES   : {excluded_samples:,}")
    print(f"  NON-AROUSAL        : {non_arousal_samples:,}")
    print(f"  AROUSAL            : {arousal_samples:,}")

    print()
    print(f"  SCORED %           : {scored_samples / total_samples * 100:.2f}%")
    print(f"  EXCLUDED %         : {excluded_samples / total_samples * 100:.2f}%")
    print(f"  NON-AROUSAL %      : {non_arousal_samples / total_samples * 100:.2f}%")
    print(f"  AROUSAL %          : {arousal_samples / total_samples * 100:.2f}%")

    print()
    print("=" * 70)
    print("RECORD SUMMARY")
    print("=" * 70)

    for r in results:
        print(
            f"{r['record_id']}: "
            f"arousal={r['arousal_pct']:.2f}% | "
            f"excluded={r['excluded_pct']:.2f}% | "
            f"scored={r['scored_pct']:.2f}%"
        )


if __name__ == "__main__":
    main()