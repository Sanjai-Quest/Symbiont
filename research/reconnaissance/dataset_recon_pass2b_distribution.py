import os
import csv
from collections import defaultdict, Counter
from statistics import median

OUTPUT_DIR = r"S:\Symbiont\research\reconnaissance\outputs"

STAGE_FILE = os.path.join(
    OUTPUT_DIR,
    "dataset_stage_duration_analysis.csv"
)

RECORD_FILE = os.path.join(
    OUTPUT_DIR,
    "dataset_stage_epoch_analysis.csv"
)

STAGE_OUTPUT = os.path.join(
    OUTPUT_DIR,
    "dataset_stage_distribution_summary.csv"
)

SUBSET_OUTPUT = os.path.join(
    OUTPUT_DIR,
    "dataset_subset_distribution_summary.csv"
)


def load_csv(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def format_hours(seconds):
    return seconds / 3600.0


def percentile_median(values):
    if not values:
        return 0.0
    return median(values)


stage_rows = load_csv(STAGE_FILE)
record_rows = load_csv(RECORD_FILE)

# ---------------------------------------------------------------------
# 1. Aggregate stage-level information
# ---------------------------------------------------------------------

stage_data = defaultdict(
    lambda: {
        "records": set(),
        "annotation_count": 0,
        "duration_sec": 0.0,
        "exact_30sec_count": 0,
        "non_30sec_count": 0,
        "per_record_duration": defaultdict(float),
        "per_record_epochs": defaultdict(int),
    }
)

for row in stage_rows:

    stage = row["stage"]
    record = row["record"]

    annotation_count = int(row["annotation_count"])
    duration_sec = float(row["total_duration_sec"])
    exact_30sec_count = int(row["exact_30sec_count"])
    non_30sec_count = int(row["non_30sec_count"])

    data = stage_data[stage]

    data["records"].add(record)
    data["annotation_count"] += annotation_count
    data["duration_sec"] += duration_sec
    data["exact_30sec_count"] += exact_30sec_count
    data["non_30sec_count"] += non_30sec_count

    data["per_record_duration"][record] += duration_sec
    data["per_record_epochs"][record] += exact_30sec_count


# ---------------------------------------------------------------------
# 2. Calculate total annotated duration
# ---------------------------------------------------------------------

total_stage_duration = sum(
    data["duration_sec"]
    for data in stage_data.values()
)

total_exact_epochs = sum(
    data["exact_30sec_count"]
    for data in stage_data.values()
)


# ---------------------------------------------------------------------
# 3. Stage distribution summary
# ---------------------------------------------------------------------

summary_rows = []

for stage in sorted(stage_data.keys()):

    data = stage_data[stage]

    duration_values = list(
        data["per_record_duration"].values()
    )

    epoch_values = list(
        data["per_record_epochs"].values()
    )

    records_with_stage = len(data["records"])

    records_with_zero_epochs = 197 - len(
        [
            value
            for value in epoch_values
            if value > 0
        ]
    )

    summary_rows.append(
        {
            "stage": stage,
            "records_with_stage": records_with_stage,
            "total_annotation_count": data["annotation_count"],
            "total_duration_hours": round(
                format_hours(data["duration_sec"]),
                4
            ),
            "percentage_of_all_annotated_time": round(
                100 * data["duration_sec"] / total_stage_duration,
                4
            ),
            "exact_30sec_epoch_count": data["exact_30sec_count"],
            "percentage_of_all_exact_30sec_epochs": round(
                100 * data["exact_30sec_count"] / total_exact_epochs,
                4
            ),
            "non_30sec_annotation_count": data["non_30sec_count"],
            "min_hours_per_record": round(
                format_hours(min(duration_values)),
                4
            ) if duration_values else 0,
            "median_hours_per_record": round(
                format_hours(percentile_median(duration_values)),
                4
            ) if duration_values else 0,
            "max_hours_per_record": round(
                format_hours(max(duration_values)),
                4
            ) if duration_values else 0,
            "min_epochs_per_record": min(epoch_values)
            if epoch_values else 0,
            "median_epochs_per_record": int(
                percentile_median(epoch_values)
            ) if epoch_values else 0,
            "max_epochs_per_record": max(epoch_values)
            if epoch_values else 0,
            "records_with_zero_exact_30sec_epochs": records_with_zero_epochs,
        }
    )


with open(
    STAGE_OUTPUT,
    "w",
    encoding="utf-8",
    newline=""
) as f:

    fieldnames = list(summary_rows[0].keys())

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(summary_rows)


# ---------------------------------------------------------------------
# 4. Subset-level analysis
# ---------------------------------------------------------------------

subset_stage_data = defaultdict(
    lambda: defaultdict(
        lambda: {
            "duration_sec": 0.0,
            "epochs": 0,
            "records": set(),
        }
    )
)

for row in stage_rows:

    subset = row["subset"]
    stage = row["stage"]
    record = row["record"]

    subset_stage_data[subset][stage]["duration_sec"] += float(
        row["total_duration_sec"]
    )

    subset_stage_data[subset][stage]["epochs"] += int(
        row["exact_30sec_count"]
    )

    subset_stage_data[subset][stage]["records"].add(record)


subset_rows = []

for subset in sorted(subset_stage_data.keys()):

    subset_total_duration = sum(
        stage["duration_sec"]
        for stage in subset_stage_data[subset].values()
    )

    subset_total_epochs = sum(
        stage["epochs"]
        for stage in subset_stage_data[subset].values()
    )

    for stage in sorted(subset_stage_data[subset].keys()):

        data = subset_stage_data[subset][stage]

        subset_rows.append(
            {
                "subset": subset,
                "stage": stage,
                "records_with_stage": len(data["records"]),
                "total_duration_hours": round(
                    format_hours(data["duration_sec"]),
                    4
                ),
                "percentage_of_subset_annotated_time": round(
                    100 * data["duration_sec"] / subset_total_duration,
                    4
                ),
                "exact_30sec_epoch_count": data["epochs"],
                "percentage_of_subset_exact_30sec_epochs": round(
                    100 * data["epochs"] / subset_total_epochs,
                    4
                ),
            }
        )


with open(
    SUBSET_OUTPUT,
    "w",
    encoding="utf-8",
    newline=""
) as f:

    fieldnames = list(subset_rows[0].keys())

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(subset_rows)


# ---------------------------------------------------------------------
# 5. Record-level usable epoch statistics
# ---------------------------------------------------------------------

usable_epochs = [
    int(row["usable_30sec_epoch_count"])
    for row in record_rows
    if row["status"] == "OK"
]

print("=" * 80)
print("PASS 2B DISTRIBUTION ANALYSIS")
print("=" * 80)

print()
print("RECORD SUMMARY")
print("-" * 80)

print("Records:", len(record_rows))
print("Minimum usable 30-sec epochs:", min(usable_epochs))
print("Median usable 30-sec epochs:", int(median(usable_epochs)))
print("Maximum usable 30-sec epochs:", max(usable_epochs))

print()
print("DATASET-WIDE STAGE DISTRIBUTION")
print("-" * 80)

print(
    f"{'Stage':25}"
    f"{'Records':>10}"
    f"{'Hours':>12}"
    f"{'% Time':>10}"
    f"{'30-sec Epochs':>15}"
    f"{'% Epochs':>12}"
)

for row in summary_rows:

    print(
        f"{row['stage']:25}"
        f"{row['records_with_stage']:>10}"
        f"{row['total_duration_hours']:>12.2f}"
        f"{row['percentage_of_all_annotated_time']:>10.2f}"
        f"{row['exact_30sec_epoch_count']:>15}"
        f"{row['percentage_of_all_exact_30sec_epochs']:>12.2f}"
    )

print()
print("TOTAL ANNOTATED TIME:")
print(
    round(
        format_hours(total_stage_duration),
        2
    ),
    "hours"
)

print()
print("TOTAL EXACT 30-SECOND ANNOTATIONS:")
print(total_exact_epochs)

print()
print("PER-STAGE DURATION LIMITS")
print("-" * 80)

for row in summary_rows:

    print()
    print(row["stage"])

    print(
        "  Records containing stage:",
        row["records_with_stage"]
    )

    print(
        "  Duration per record:",
        row["min_hours_per_record"],
        "h minimum |",
        row["median_hours_per_record"],
        "h median |",
        row["max_hours_per_record"],
        "h maximum"
    )

    print(
        "  Exact 30-sec epochs per record:",
        row["min_epochs_per_record"],
        "minimum |",
        row["median_epochs_per_record"],
        "median |",
        row["max_epochs_per_record"],
        "maximum"
    )

    print(
        "  Records with zero exact 30-sec epochs:",
        row["records_with_zero_exact_30sec_epochs"]
    )


print()
print("SUBSET COMPARISON")
print("-" * 80)

for subset in sorted(subset_stage_data.keys()):

    print()
    print(subset)

    subset_rows_here = [
        row
        for row in subset_rows
        if row["subset"] == subset
    ]

    for row in subset_rows_here:

        print(
            f"  {row['stage']:25}"
            f"{row['total_duration_hours']:>10.2f} h"
            f"  {row['percentage_of_subset_annotated_time']:>7.2f}%"
            f"  {row['exact_30sec_epoch_count']:>7} epochs"
            f"  {row['percentage_of_subset_exact_30sec_epochs']:>7.2f}%"
        )


print()
print("OUTPUT FILES")
print("-" * 80)
print(STAGE_OUTPUT)
print(SUBSET_OUTPUT)

print()
print("=" * 80)
print("PASS 2B DISTRIBUTION ANALYSIS COMPLETE")
print("=" * 80)