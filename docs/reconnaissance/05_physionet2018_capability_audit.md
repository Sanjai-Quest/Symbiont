\# PhysioNet/CinC Challenge 2018

\## Dataset Capability Audit for Symbiont



\*\*Project:\*\* Symbiont  

\*\*Dataset:\*\* PhysioNet/CinC Challenge 2018 Sleep Arousal Detection  

\*\*Dataset version:\*\* 1.0.0  

\*\*Audit status:\*\* PASS WITH IMPLEMENTATION-LEVEL VERIFICATION PENDING  

\*\*Primary dataset role:\*\* Sleep-disruption event detection and attribution



\---



\## 1. Purpose



This audit determines whether the PhysioNet/CinC Challenge 2018 dataset contains the physiological signals, sleep-stage information, event annotations, and temporal alignment required to build the Symbiont sleep-disruption analysis pipeline.



The purpose of this audit is dataset feasibility, not model evaluation.



No claim is made here that Symbiont can diagnose a medical condition.



\---



\## 2. Symbiont Product Requirement



Symbiont is intended to analyze overnight physiological recordings and answer:



> What physiological events disrupted the person's sleep during the night?



The planned system requires:



1\. Multimodal overnight physiological signals.

2\. Sleep-stage information.

3\. Physiological event annotations.

4\. Temporal alignment between signals and annotations.

5\. Sufficient data to reconstruct a night-level disruption timeline.

6\. A basis for later event-attribution modelling.



\---



\## 3. Dataset-Level Reconnaissance



The official PhysioNet dataset record listing was inspected.



Verified dataset record counts:



\- Total records: 1,983

\- Training records: 994

\- Test records: 989



The training records contain expert annotations and are therefore the relevant portion for supervised development.



The complete dataset should not be downloaded indiscriminately during early development because the full dataset is very large. Controlled acquisition will be used during initial development.



\---



\## 4. Representative Training Record



Record inspected:



`tr03-0005`



Official PSG header inspection established:



\- Channels: 13

\- Sampling frequency: 200 Hz

\- Samples: 5,147,000

\- Approximate recording duration: 7.15 hours



\### Physiological channels



The record contains:



| Category | Channels |

|---|---|

| EEG | F3-M2, F4-M1, C3-M2, C4-M1, O1-M2, O2-M1 |

| EOG | E1-M2 |

| Chin EMG | Chin1-Chin2 |

| Respiration | ABD, CHEST, AIRFLOW |

| Oxygen | SaO2 |

| Cardiac | ECG |



This provides multimodal physiological information covering neural activity, eye movement, muscle activity, respiration, oxygen saturation, and cardiac activity.



\---



\## 5. Arousal Annotation Structure



The corresponding annotation file was inspected:



`tr03-0005-arousal.mat`



The file is MATLAB v7.3 and therefore uses HDF5 internally.



The root structure contains:



```text

\#refs#

data/

```



Inside `data`:



```text

arousals

sleep\_stages/

```



The `arousals` dataset has:



```text

Shape: (5,147,000,)

Data type: float64

Minimum: -1

Maximum: 1

Unique values: -1, 0, +1

Non-zero samples: 2,791,129

```



Most importantly:



```text

PSG samples:       5,147,000

Arousal samples:   5,147,000

Sampling rate:     200 Hz

```



Therefore, the inspected arousal representation has the same sample length as the corresponding PSG recording.



This provides strong evidence that the annotation representation is sample-aligned with the physiological recording.



\### Important limitation



The exact semantic meaning of the numeric values `-1`, `0`, and `+1` has not yet been formally decoded.



The values must not be assigned meanings by assumption.



Their semantic decoding will be handled during implementation of the annotation parser and verified against the official challenge representation.



\---



\## 6. Sleep-Stage Structure



The inspected annotation file contains six sleep-stage datasets:



```text

data/

└── sleep\_stages/

&#x20;   ├── nonrem1

&#x20;   ├── nonrem2

&#x20;   ├── nonrem3

&#x20;   ├── rem

&#x20;   ├── undefined

&#x20;   └── wake

```



Each dataset has:



```text

Shape: 1 × 5,147,000

Data type: uint8

Values: 0 and 1

```



Therefore, each stage is represented as a binary sample-level mask.



\### Observed distribution for tr03-0005



| Stage | Samples marked 1 | Approx. duration |

|---|---:|---:|

| N1 | 348,000 | 29.0 min |

| N2 | 1,602,000 | 133.5 min |

| N3 | 432,000 | 36.0 min |

| REM | 486,000 | 40.5 min |

| Wake | 2,207,000 | 183.9 min |

| Undefined | 72,000 | 6.0 min |



Duration calculations use:



```text

duration = samples / 200 Hz

```



These distributions are observations from the inspected record and are not presented as population-level statistics for the entire dataset.



\---



\## 7. Explicit Event Labels



Inspection of the corresponding `.arousal` annotation text established the presence of explicit physiological event labels.



Observed labels included:



\- `resp\_centralapnea`

\- `resp\_obstructiveapnea`

\- `resp\_hypopnea`

\- `arousal\_rera`



This confirms that the dataset is not limited to generic sleep-stage labels.



It contains event-level information relevant to sleep-disruption analysis.



The complete event taxonomy and exact numerical encoding will be verified during annotation-parser implementation.



\---



\## 8. Dataset-to-Product Compatibility



\### Requirement 1: Multimodal physiological signals



\*\*Status: PASS\*\*



The inspected training record contains EEG, EOG, EMG, respiration, oxygen saturation, and ECG.



\---



\### Requirement 2: Sleep architecture



\*\*Status: PASS\*\*



The inspected annotation file provides sample-level masks for:



\- N1

\- N2

\- N3

\- REM

\- Wake

\- Undefined



\---



\### Requirement 3: Physiological event annotations



\*\*Status: PASS\*\*



The inspected `.arousal` annotation contains explicit event labels including respiratory events and RERA.



\---



\### Requirement 4: Temporal alignment



\*\*Status: STRONG PASS FOR INSPECTED RECORD\*\*



The PSG contains 5,147,000 samples at 200 Hz.



The corresponding arousal annotation contains exactly 5,147,000 samples.



Every sleep-stage mask also contains exactly 5,147,000 samples.



This establishes sample-length alignment for the inspected record.



A parser-level verification will still be required before production processing.



\---



\### Requirement 5: Sleep-disruption timeline



\*\*Status: FEASIBLE\*\*



The combination of:



```text

physiological signals

\+

sleep-stage masks

\+

event annotations

\+

sample-level alignment

```



provides the required structural basis for constructing an overnight temporal event timeline.



\---



\### Requirement 6: Disruption attribution



\*\*Status: FEASIBLE, MODELING NOT YET PROVEN\*\*



The dataset provides enough information to investigate relationships between:



\- physiological events,

\- sleep stages,

\- arousals,

\- and temporal sleep fragmentation.



However, the actual attribution methodology is a modelling problem and has not yet been validated.



The dataset audit does not claim that causal attribution is already solved.



\---



\## 9. What This Audit Proves



Based on the evidence collected so far, the PhysioNet/CinC Challenge 2018 dataset provides the fundamental data structures required for the planned Symbiont pipeline.



The strongest evidence is the alignment observed in `tr03-0005`:



```text

5,147,000 PSG samples

&#x20;       │

&#x20;       ├── 13 physiological channels

&#x20;       │

&#x20;       ├── 5,147,000 arousal annotation samples

&#x20;       │

&#x20;       └── 5,147,000 samples for each sleep-stage mask

```



Therefore, Symbiont does not need to invent a synthetic physiological dataset merely to establish the initial product pipeline.



The existing dataset provides real multimodal PSG recordings with expert-derived annotations suitable for supervised development.



\---



\## 10. What This Audit Does NOT Prove



This audit does not establish:



1\. Final model accuracy.

2\. Generalization to unseen populations.

3\. Clinical validity.

4\. Medical diagnostic capability.

5\. Causal relationships between detected events and awakenings.

6\. Exact semantics of every numerical annotation value.

7\. Performance on the complete dataset.

8\. That every record has identical annotation structure without further validation.



These questions belong to later validation stages.



\---



\## 11. Dataset Decision



\### Decision



\*\*PhysioNet/CinC Challenge 2018 is accepted as the primary development dataset for Symbiont.\*\*



Sleep-EDF Expanded remains a supporting dataset for sleep-architecture and physiological-processing development.



The project will not treat Sleep-EDF as the primary source of respiratory-event labels because its available annotations do not provide the same explicit event-label structure required for the central product objective.



\---



\## 12. Next Phase



The reconnaissance phase for this representative record is considered complete.



The next phase is controlled dataset acquisition and implementation.



Planned sequence:



```text

1\. Define controlled training subset

&#x20;       ↓

2\. Download required records

&#x20;       ↓

3\. Build annotation parser

&#x20;       ↓

4\. Verify signal/annotation alignment programmatically

&#x20;       ↓

5\. Build preprocessing pipeline

&#x20;       ↓

6\. Build sleep-stage representation

&#x20;       ↓

7\. Build physiological-event representation

&#x20;       ↓

8\. Construct temporal disruption timeline

&#x20;       ↓

9\. Develop disruption-attribution logic

&#x20;       ↓

10\. Evaluate on held-out records

```



No full-dataset download will be performed until the minimum development subset and processing architecture are defined.



\---



\## 13. Evidence Artifacts



Relevant reconnaissance artifacts include:



```text

research/reconnaissance/

├── dataset\_recon.py

├── dataset\_recon\_pass2.py

├── dataset\_recon\_pass2b.py

├── dataset\_recon\_pass2b\_distribution.py

├── inspect\_annotation\_durations.py

├── inspect\_pass2\_cases.py

├── dataset\_capability\_audit.py

├── dataset\_label\_epoch\_audit.py

├── product\_compatibility\_audit.py

└── inspect\_event\_marker.py

```



The inspected PhysioNet annotation file:



```text

research/reconnaissance/tr03-0005-arousal.mat

```



\---



\## 14. Audit Conclusion



\*\*PASS WITH IMPLEMENTATION-LEVEL VERIFICATION PENDING\*\*



The inspected PhysioNet/CinC Challenge 2018 record provides the core data required for Symbiont's planned sleep-disruption analysis architecture.



The dataset contains real multimodal PSG signals, sample-level sleep-stage masks, explicit physiological event annotations, and matching sample dimensions between the physiological recording and annotation structures.



The next engineering objective is therefore no longer dataset feasibility.



It is to build and verify the first reproducible Symbiont processing pipeline.

