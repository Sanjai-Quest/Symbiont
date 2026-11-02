import os
import numpy as np
import mne


DATASET_ROOT = r"S:\Symbiont\Datasets\raw\sleep-edfx-1.0.0\sleep-edf-database-expanded-1.0.0"


def find_psg_files():
    files = []

    for subset in ["sleep-cassette", "sleep-telemetry"]:
        subset_path = os.path.join(DATASET_ROOT, subset)

        for filename in sorted(os.listdir(subset_path)):
            if filename.endswith("-PSG.edf"):
                files.append(
                    os.path.join(subset_path, filename)
                )

    return files


def inspect_event_marker(psg_path):

    record = os.path.basename(psg_path)

    raw = mne.io.read_raw_edf(
        psg_path,
        preload=False,
        verbose=False
    )

    event_channels = [
        ch for ch in raw.ch_names
        if "event" in ch.lower()
    ]

    print("=" * 70)
    print(f"RECORD: {record}")
    print("=" * 70)

    print("Event-like channels:", event_channels)

    if not event_channels:
        print("RESULT: No event-like channel found.")
        return

    for channel in event_channels:

        data = raw.get_data(
            picks=[channel],
            start=0,
            stop=raw.n_times
        )[0]

        finite = data[np.isfinite(data)]

        if len(finite) == 0:
            print(f"{channel}: NO FINITE DATA")
            continue

        unique_values = np.unique(finite)

        print(f"\nCHANNEL: {channel}")
        print(f"Samples: {len(data):,}")
        print(f"Min: {finite.min()}")
        print(f"Max: {finite.max()}")
        print(f"Mean: {finite.mean()}")
        print(f"Non-zero samples: {np.count_nonzero(finite):,}")
        print(f"Unique values: {len(unique_values):,}")

        if len(unique_values) <= 20:
            print("Unique values:")
            print(unique_values)

        else:
            print(
                "Unique values: too many to display"
            )


def main():

    files = find_psg_files()

    print("=" * 70)
    print("SYMBIONT EVENT MARKER INSPECTION")
    print("=" * 70)
    print(f"PSG files discovered: {len(files)}")
    print()

    for index, psg_path in enumerate(files, start=1):

        print(
            f"[{index}/{len(files)}]"
        )

        try:
            inspect_event_marker(psg_path)

        except Exception as exc:

            print(
                f"ERROR: {repr(exc)}"
            )

        print()


if __name__ == "__main__":
    main()