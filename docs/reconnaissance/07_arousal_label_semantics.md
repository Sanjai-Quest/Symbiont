\# PhysioNet Challenge 2018 Arousal Label Semantics



\*\*Project:\*\* Symbiont  

\*\*Dataset:\*\* PhysioNet/CinC Challenge 2018 Sleep Arousal Detection  

\*\*Record investigated:\*\* `tr03-0005`  

\*\*Status:\*\* Verified



\---



\## 1. Purpose



This investigation determines the exact meaning of the sample-level values stored in:



```text

tr03-0005-arousal.mat

```



The dataset contains an `arousals` vector with three possible values:



```text

\-1

&#x20;0

+1

```



The purpose was to determine their semantics from evidence rather than assuming their meaning from the numeric values.



\---



\## 2. Initial Observation



The HDF5 annotation file contained:



```text

data/

├── arousals

└── sleep\_stages/

&#x20;   ├── nonrem1

&#x20;   ├── nonrem2

&#x20;   ├── nonrem3

&#x20;   ├── rem

&#x20;   ├── undefined

&#x20;   └── wake

```



For `tr03-0005`:



```text

PSG samples:       5,147,000

Arousal samples:   5,147,000

Sleep-stage masks: 5,147,000

Sampling rate:     200 Hz

```



The matching lengths establish structural sample alignment.



They do not, by themselves, establish semantic meaning.



\---



\## 3. Observed Value Distribution



The `arousals` vector contained:



| Value | Samples |

|---:|---:|

| `-1.0` | 2,605,102 |

| `0.0` | 2,355,871 |

| `+1.0` | 186,027 |

| \*\*Total\*\* | \*\*5,147,000\*\* |



\---



\## 4. Annotation File Investigation



The corresponding `.arousal` file could not be decoded as UTF-8.



Raw-byte inspection showed that it is a binary annotation format containing embedded annotation names and:



```text

\## time resolution: 200

```



WFDB successfully parsed the file using:



```python

wfdb.rdann(record, "arousal")

```



The record contained 240 annotation entries.



Examples of parsed annotations included:



```text

W

N1

N2

resp\_centralapnea

arousal\_rera

```



The annotation file therefore contains event/stage information separate from the sample-level `arousals` vector.



\---



\## 5. Verification Against RERA Events



Two `arousal\_rera` intervals were identified:



\### RERA #1



```text

Start: 192,904

End:   196,364

Duration: 3,460 samples

Duration: 17.30 seconds

```



The corresponding HDF5 arousal values were:



```text

+1 = 3,460 samples

```



Therefore the entire annotated RERA interval was represented as `+1`.



\### RERA #2



```text

Start: 199,652

End:   203,231

Duration: 3,579 samples

Duration: 17.895 seconds

```



The corresponding HDF5 arousal values were:



```text

+1 = 3,579 samples

```



Again, the entire annotated RERA interval was represented as `+1`.



This provides direct local evidence that `+1` represents an arousal-positive region.



\---



\## 6. Verification of Zero Regions



The `0` value occurred in 72 contiguous regions in `tr03-0005`.



These regions varied substantially in duration.



Examples:



```text

0–69,998

≈ 349.99 seconds



351,494–795,507

≈ 2,220.065 seconds



198,364–199,251

≈ 4.435 seconds

```



Therefore `0` is not merely a short boundary artifact between events.



The zero state represents a legitimate sample-level state.



\---



\## 7. Important Correction During Investigation



An initial working hypothesis incorrectly assumed:



```text

\-1 = non-arousal

&#x20;0 = unknown/transition

+1 = arousal

```



This hypothesis was rejected.



A region associated with ordinary `W → N1` sleep-stage annotations contained `-1`, demonstrating that `-1` could not simply mean non-arousal.



Further investigation of the RERA intervals established the `+1` relationship.



The official Challenge 2018 definition was then consulted.



\---



\## 8. Authoritative Definition



The official PhysioNet Challenge 2018 specification defines the sample-level arousal target as:



```text

+1 = arousal region

&#x20;0 = non-arousal region

\-1 = region that will not be scored

```



Therefore the final interpretation is:



| Value | Meaning |

|---:|---|

| `+1` | Target arousal region |

| `0` | Target non-arousal region |

| `-1` | Excluded / not scored |



\---



\## 9. Important Distinction



The `.arousal` annotation file and the `\*-arousal.mat` target vector must \*\*not\*\* be treated as interchangeable.



The `.arousal` file contains the underlying annotation/event structure, including sleep stages and physiological events.



The `arousals` vector provides the Challenge's precomputed sample-level target regions.



Therefore Symbiont should not simply convert every event in `.arousal` into a positive arousal label.



The official target definition must be respected.



\---



\## 10. Implication for Symbiont



For supervised arousal detection, the target representation should be interpreted as:



```text

+1

↓

positive arousal target



0

↓

negative/non-arousal target



\-1

↓

excluded from supervised scoring/training

```



The `-1` samples should not automatically be converted to negative examples.



Doing so would introduce incorrect training labels because those regions are explicitly excluded from scoring.



\---



\## 11. Verified Record Structure



For `tr03-0005`:



```text

PSG:

5,147,000 samples

200 Hz

13 channels



Arousal target:

5,147,000 samples

float64

values: -1, 0, +1



Sleep-stage masks:

5,147,000 samples each

uint8

```



This establishes a sample-aligned multimodal record containing:



```text

Physiological signals

&#x20;       +

Sleep-stage information

&#x20;       +

Sample-level arousal target

```



\---



\## 12. Current Status



\*\*PASS\*\*



The semantics of the PhysioNet Challenge 2018 sample-level arousal target have been established using:



1\. Local file inspection

2\. HDF5 structure inspection

3\. WFDB annotation parsing

4\. Direct comparison against annotated RERA intervals

5\. Official Challenge documentation



No semantic assumption remains for `-1`, `0`, or `+1`.



\---



\## 13. Next Engineering Phase



The next phase is not model development.



First, the remaining development records must be validated for:



\- signal/sample length consistency

\- channel configuration

\- sampling frequency

\- arousal-vector length

\- sleep-stage-vector length

\- `-1 / 0 / +1` distribution

\- file integrity



After validation, Symbiont will implement a reproducible record parser that converts each raw PhysioNet record into a unified internal representation.



\---



\## Evidence



Primary local evidence:



```text

Datasets/raw/physionet-challenge-2018/

training/tr03-0005/

```



Relevant files:



```text

tr03-0005.hea

tr03-0005.mat

tr03-0005.arousal

tr03-0005-arousal.mat

```



Relevant tools:



```text

WFDB

h5py

NumPy

```



Official dataset:



PhysioNet/CinC Challenge 2018 Sleep Arousal Detection.

