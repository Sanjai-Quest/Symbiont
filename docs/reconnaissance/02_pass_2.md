# Symbiont - Dataset Reconnaissance Pass 2

## Project

**Project:** Symbiont
**Dataset:** Sleep-EDF Expanded v1.0.0
**Phase:** Dataset Foundation and Integrity / Reconnaissance
**Pass:** 2
**Status:** Complete and validated
**Model development:** Not started

---

## 1. Objective

Pass 2 was performed to determine whether the PSG recordings and their corresponding hypnogram annotations are temporally compatible and to characterize the raw sleep-stage annotation structure before preprocessing.

The pass specifically investigated:

- PSG recording duration versus hypnogram duration.
- Annotation gaps and overlaps.
- Annotations extending beyond the available PSG recording.
- Raw sleep-stage labels present in the dataset.
- Exact 30-second annotations that are fully contained within the PSG recording.
- Differences between the sleep-cassette and sleep-telemetry subsets.
- The treatment of unscored (`Sleep stage ?`) and movement annotations.
- Preservation of raw Stage 3 and Stage 4 labels before later normalization.

No machine-learning model was trained during this pass.

---

## 2. Dataset and Tools

### Dataset

Sleep-EDF Expanded v1.0.0 from PhysioNet.

Local dataset root:

```text
S:\Symbiont\Datasets\raw\sleep-edfx-1.0.0\sleep-edf-database-expanded-1.0.0
```

The dataset contains two relevant subsets:

```text
sleep-cassette
sleep-telemetry
```

A total of **197 PSG/Hypnogram pairs** were identified.

### Software

- Python
- MNE-Python 1.13.2
- CSV-based analysis outputs

### Scripts

```text
research/reconnaissance/dataset_recon_pass2.py
research/reconnaissance/dataset_recon_pass2b.py
research/reconnaissance/dataset_recon_pass2b_distribution.py
research/reconnaissance/inspect_pass2_cases.py
```

Generated outputs are stored under:

```text
research/reconnaissance/outputs/
```

Generated outputs are excluded from Git because they are reproducible analysis artifacts.

---

## 3. Pass 2A - PSG and Hypnogram Temporal Alignment

### 3.1 Processing result

All 197 PSG/Hypnogram pairs were successfully read.

```text
Records processed: 197
Successful:         197
Errors:               0
```

### 3.2 Duration comparison

The hypnogram duration does not consistently equal the PSG recording duration.

Dataset-wide results:

```text
Records:                          197
Minimum duration difference:   -4939.99 sec
Maximum duration difference:   25200.01 sec
Mean duration difference:       3384.782 sec
Median duration difference:     3000.01 sec
```

The difference was not uniform across the dataset.

Some cassette recordings have hypnograms extending beyond the PSG recording, while some telemetry recordings have hypnograms ending before the PSG recording.

This means that hypnogram duration must not be assumed to represent the available physiological signal duration.

### 3.3 Annotation gaps and overlaps

```text
Records with annotation gaps:       2
Records with annotation overlaps:    0
```

The two records with gaps were:

```text
ST7121J0
ST7221J0
```

The observed gaps were approximately:

```text
ST7121J0: 119.99 sec
ST7221J0:  19.99 sec
```

No annotation overlaps were detected.

### 3.4 Annotations beyond the PSG boundary

```text
Records with annotations beyond PSG: 159
Maximum beyond-PSG annotation count: 2
```

This finding was investigated rather than automatically classified as corruption.

Targeted inspection showed that cassette examples can contain hypnogram annotations extending to the 24-hour annotation boundary after the physiological recording has ended.

For example:

```text
SC4001E0
PSG end: approximately 79,500 sec
Hypnogram end: 86,400 sec
```

The final annotation was:

```text
Sleep stage ?
```

covering the period after the PSG ended.

Another example:

```text
SC4592G0
PSG end: approximately 61,200 sec
Hypnogram end: 86,400 sec
```

Again, the post-PSG period was represented as `Sleep stage ?`.

This supports using the **actual PSG recording boundary** as the physiological validity boundary during preprocessing.

---

## 4. Targeted Temporal Inspection

Four records were inspected in detail because they represented different alignment patterns:

```text
SC4001E0
SC4592G0
ST7192J0
ST7121J0
```

### SC4001E0

- PSG duration: 79,499.99 sec
- Hypnogram duration: 86,400 sec
- Difference: +6,900.01 sec
- Final annotation: `Sleep stage ?`
- Post-PSG unknown period: 6,900 sec

### SC4592G0

- PSG duration: 61,199.99 sec
- Hypnogram duration: 86,400 sec
- Difference: +25,200.01 sec
- Final annotation: `Sleep stage ?`
- Post-PSG unknown period: 25,200 sec

### ST7192J0

- PSG duration: 32,899.99 sec
- Hypnogram duration: 27,960 sec
- Difference: -4,939.99 sec
- No `Sleep stage ?` annotations

### ST7121J0

- PSG duration: 31,199.99 sec
- Hypnogram duration: 31,080 sec
- Difference: -119.99 sec
- One annotation gap
- No `Sleep stage ?` annotations

### Interpretation

The duration mismatch is structured rather than evidence of random annotation corruption.

The preprocessing pipeline therefore must explicitly respect the PSG recording boundary rather than requiring equal PSG and hypnogram durations.

---

## 5. Pass 2B - Raw Sleep-Stage Structure

The raw annotation labels encountered across the 197 records were:

```text
Movement time
Sleep stage 1
Sleep stage 2
Sleep stage 3
Sleep stage 4
Sleep stage ?
Sleep stage R
Sleep stage W
```

Record-level presence counts:

| Raw annotation | Records containing it |
|---|---:|
| Movement time | 59 |
| Sleep stage 1 | 197 |
| Sleep stage 2 | 197 |
| Sleep stage 3 | 178 |
| Sleep stage 4 | 118 |
| Sleep stage ? | 150 |
| Sleep stage R | 197 |
| Sleep stage W | 197 |

These are **record-level presence counts**, not epoch counts.

---

## 6. Meaning of `Sleep stage ?`

The `Sleep stage ?` label is treated as an unscored/unknown annotation during this reconnaissance.

Targeted cassette inspection showed that large `Sleep stage ?` regions can occur after the actual PSG recording has ended and extend to the 24-hour hypnogram boundary.

Therefore, `Sleep stage ?` must not be interpreted as an additional sleep stage for Symbiont.

For later supervised preprocessing, it will be excluded from target labels.

Importantly, the raw label is preserved during reconnaissance so that the original annotation structure remains traceable.

---

## 7. Stage 3 and Stage 4 Handling

The dataset uses separate raw annotations:

```text
Sleep stage 3
Sleep stage 4
```

These labels are preserved separately during reconnaissance.

No Stage 3/Stage 4 merging was performed in Pass 2.

The planned later preprocessing normalization is:

```text
Sleep stage W  -> W
Sleep stage 1  -> N1
Sleep stage 2  -> N2
Sleep stage 3  -> N3
Sleep stage 4  -> N3
Sleep stage R  -> REM
Sleep stage ?  -> exclude
Movement time  -> exclude
```

The Stage 3 + Stage 4 to N3 transformation is therefore a **preprocessing decision**, not a raw-data reconnaissance modification.

---

## 8. Exact 30-Second Epoch Analysis

Sleep-EDF annotations are commonly represented using 30-second sleep-scoring intervals. For this analysis, an annotation was counted as an exact 30-second annotation when its duration was 30.0 seconds within the analysis tolerance.

A usable exact 30-second annotation was required to be completely contained within the actual PSG recording.

The PSG boundary was defined as:

```python
psg_end = raw.times[-1] + (1 / raw.info["sfreq"])
```

This is important because `raw.times[-1]` represents the timestamp of the final sample, not the end boundary of the complete final sample interval.

### Final validated count

```text
Exact 30-second annotations fully inside PSG: 10,258
```

The same value was independently obtained from the stage-level aggregation:

```text
Stage-analysis exact 30-second annotations: 10,258
```

Difference:

```text
0
```

---

## 9. Validation Bug and Correction

### Initial result

The first Pass 2B implementation reported:

```text
10,257
```

usable exact 30-second annotations.

### Investigation

A separate aggregation reported:

```text
10,258
```

A boundary scan confirmed that there were **zero** exact 30-second annotations outside the PSG recordings.

The discrepancy was then isolated to one record:

```text
SC4092E0
```

For this record:

```text
Record-level count: 40
Stage-level count:  41
```

Direct inspection showed:

```text
PSG end: 85740.0 sec
```

and the final exact 30-second annotation was:

```text
Sleep stage W
85710.0 -> 85740.0
```

The annotation ended exactly at the PSG boundary.

The original record-level calculation used `raw.times[-1]`, which is the final sample timestamp and is slightly less than the full recording boundary. Consequently, the final 30-second interval was incorrectly rejected.

### Correction

The PSG boundary calculation was corrected to:

```python
psg_end = raw.times[-1] + (1 / raw.info["sfreq"])
```

The corrected script was rerun across all 197 records.

### Final validation

```text
Records: 197
Status OK: 197
Usable exact 30-second epochs inside PSG: 10258
Exact 30-second annotations across stage analysis: 10258
Difference: 0
```

The discrepancy is therefore resolved and documented as an analysis-code boundary error, not a dataset inconsistency.

---

## 10. Important Limitation of Earlier Stage Distribution Analysis

An earlier stage-duration distribution included the complete hypnogram annotation durations.

That analysis is useful for describing the raw annotation files, but it must **not** be interpreted as the amount of usable physiological PSG data.

In particular:

- Hypnogram annotations may extend beyond the PSG recording.
- `Sleep stage ?` may represent post-PSG unscored time.
- Movement and unknown annotations are not intended as supervised sleep-stage targets.
- The raw hypnogram duration therefore cannot be used as the model-ready data duration.

Future model-ready statistics must be calculated after applying the PSG boundary and label eligibility rules.

---

## 11. Decisions From Pass 2

### Decision 1 - PSG defines the physiological boundary

The actual PSG recording duration will define the valid physiological signal boundary.

Hypnogram annotations outside that boundary will not be treated as available physiological data.

### Decision 2 - Preserve raw labels during reconnaissance

No raw sleep-stage labels are modified during dataset reconnaissance.

### Decision 3 - Exclude unknown and movement labels later

For supervised preprocessing:

```text
Sleep stage ? -> exclude
Movement time -> exclude
```

### Decision 4 - Normalize Stage 3 and Stage 4 later

Stage 3 and Stage 4 remain separate in the raw reconnaissance outputs.

During preprocessing they will be normalized to N3.

### Decision 5 - Use exact 30-second PSG-contained intervals as the base epoch definition

The validated base count is:

```text
10,258 exact 30-second annotations fully contained within PSG
```

This count is a raw epoch-boundary statistic. It is not yet the final number of model-ready labeled epochs.

---

## 12. Outputs Produced

```text
research/reconnaissance/outputs/
â”œâ”€â”€ dataset_alignment.csv
â”œâ”€â”€ dataset_stage_summary.csv
â”œâ”€â”€ dataset_stage_epoch_analysis.csv
â””â”€â”€ dataset_stage_duration_analysis.csv
```

Scripts used:

```text
research/reconnaissance/dataset_recon_pass2.py
research/reconnaissance/dataset_recon_pass2b.py
research/reconnaissance/dataset_recon_pass2b_distribution.py
research/reconnaissance/inspect_pass2_cases.py
```

---

## 13. Failed Attempts and Fixes

### Failure 1 - Annotation iteration

Initial implementation attempted:

```python
for onset, duration, description in annotations:
```

This caused:

```text
ValueError: too many values to unpack (expected 3)
```

The implementation was corrected to explicitly combine:

```python
annotations.onset
annotations.duration
annotations.description
```

using `zip()` and sorting by onset.

### Failure 2 - PSG boundary definition

The initial exact-30-second calculation used the final sample timestamp as the recording boundary.

This caused one valid final interval in `SC4092E0` to be excluded.

The boundary was corrected to include one sample interval:

```python
raw.times[-1] + 1 / raw.info["sfreq"]
```

The final count changed from 10,257 to 10,258.

---

## 14. Pass 2 Conclusion

Pass 2 establishes that the Sleep-EDF Expanded dataset can be systematically paired and read across all 197 PSG/Hypnogram records.

The dataset contains structured differences between PSG and hypnogram duration, including annotations beyond the actual PSG boundary and a small number of annotation gaps. These differences do not prevent use of the dataset, but they require explicit boundary handling during preprocessing.

The validated raw 30-second annotation count fully contained within PSG recordings is:

**10,258.**

This number is internally consistent across the independent record-level and stage-level analyses after correcting the PSG endpoint calculation.

No model development has been performed.

The project is now ready to move from reconnaissance into a dedicated preprocessing and label-normalization phase.

---

## 15. Next Phase

The next phase will define and implement the reproducible preprocessing pipeline, including:

1. PSG boundary enforcement.
2. 30-second epoch extraction.
3. Raw-label normalization.
4. Stage 3 + Stage 4 -> N3.
5. Exclusion of `Sleep stage ?` and Movement time.
6. Signal/channel selection.
7. Signal-quality and artifact checks.
8. Final model-ready dataset accounting.

Preprocessing will be performed without modifying the original raw EDF files.
