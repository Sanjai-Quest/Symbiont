from pathlib import Path

ROOT = Path("Datasets/raw/physionet-challenge-2018/training")

for record_dir in sorted(ROOT.iterdir()):
    if not record_dir.is_dir():
        continue

    record = record_dir.name
    nested = record_dir / record

    print(f"===== {record} =====")

    for path in sorted(nested.iterdir()):
        print(f"{path.name:28} {path.stat().st_size:>12,} bytes")

print("\nLOCAL SIZE CHECK COMPLETE")
