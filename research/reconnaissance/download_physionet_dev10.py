from pathlib import Path
import urllib.request

BASE_URL = "https://physionet.org/files/challenge-2018/1.0.0/"
MANIFEST = Path("research/reconnaissance/physionet2018_dev10_records.txt")
OUTPUT_ROOT = Path("Datasets/raw/physionet-challenge-2018")

FILES = [
    ".hea",
    ".mat",
    ".arousal",
    "-arousal.mat",
]


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading: {url}")
    print(f"       -> {destination}")

    with urllib.request.urlopen(url, timeout=60) as response:
        expected_size = response.headers.get("Content-Length")
        expected_size = int(expected_size) if expected_size else None

        with open(destination, "wb") as f:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)

    actual_size = destination.stat().st_size

    if expected_size is not None and actual_size != expected_size:
        raise RuntimeError(
            f"SIZE MISMATCH: {destination} "
            f"(expected {expected_size}, got {actual_size})"
        )

    print(f"       OK ({actual_size:,} bytes)")


def main():
    records = [
        line.strip()
        for line in MANIFEST.read_text().splitlines()
        if line.strip()
    ]

    print(f"Records: {len(records)}")
    print(f"Files per record: {len(FILES)}")
    print()

    for record in records:
        record_id = record.split("/")[-1]
        print(f"===== {record_id} =====")

        for suffix in FILES:
            url = BASE_URL + record + suffix

            relative_dir = Path(record)
            destination = OUTPUT_ROOT / relative_dir / (
                record_id + suffix
            )

            download_file(url, destination)

        print()

    print("ACQUISITION COMPLETE")


if __name__ == "__main__":
    main()