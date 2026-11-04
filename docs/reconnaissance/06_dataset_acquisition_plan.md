\# Symbiont Dataset Acquisition Plan



\*\*Project:\*\* Symbiont  

\*\*Primary dataset:\*\* PhysioNet/CinC Challenge 2018 Sleep Arousal Detection  

\*\*Supporting dataset:\*\* Sleep-EDF Expanded  

\*\*Status:\*\* Planning  

\*\*Purpose:\*\* Define controlled dataset acquisition before downloading training data.



\---



\## 1. Objective



The objective of this phase is to obtain a controlled subset of the PhysioNet/CinC Challenge 2018 training dataset sufficient to build and validate the first Symbiont processing pipeline.



The project will not download the complete dataset during initial development.



The initial subset must be large enough to test:



```text

Raw PSG

&#x20;   ↓

Signal loading

&#x20;   ↓

Preprocessing

&#x20;   ↓

Sleep-stage representation

&#x20;   ↓

Physiological-event representation

&#x20;   ↓

Arousal/event timeline

&#x20;   ↓

Sleep-fragmentation analysis

&#x20;   ↓

Disruption-attribution prototype

```



\---



\## 2. Why Controlled Acquisition Is Required



The complete PhysioNet Challenge 2018 dataset is large.



Downloading the entire dataset before confirming that the processing pipeline works would create unnecessary storage, processing, and management overhead.



The development strategy is therefore:



```text

Small controlled subset

&#x20;       ↓

Pipeline validation

&#x20;       ↓

Failure correction

&#x20;       ↓

Expanded training subset

&#x20;       ↓

Model development

&#x20;       ↓

Larger-scale validation

```



This prevents large-scale data acquisition from occurring before the basic pipeline is proven.



\---



\## 3. Dataset Role



\### Primary dataset



\*\*PhysioNet/CinC Challenge 2018 Sleep Arousal Detection\*\*



Purpose:



\- physiological-event detection

\- arousal analysis

\- sleep-disruption timeline construction

\- multimodal PSG processing

\- supervised model development



\### Supporting dataset



\*\*Sleep-EDF Expanded\*\*



Purpose:



\- sleep-stage processing

\- PSG signal-processing development

\- supporting physiological analysis

\- independent development/debugging where appropriate



Sleep-EDF is not the primary source for Symbiont's explicit physiological-event detection because its annotations do not provide the same event-label structure established in the PhysioNet Challenge 2018 dataset.



\---



\## 4. Acquisition Unit



The basic acquisition unit will be a complete PhysioNet training record.



For a selected record, the required components should include the files necessary to reconstruct:



1\. physiological signals

2\. sleep-stage information

3\. event/arousal annotations

4\. record metadata/header information



A record should not be considered acquired merely because its signal file has been downloaded.



\---



\## 5. Initial Development Subset



The first acquisition should use a \*\*small controlled subset of approximately 10 training records\*\*.



The purpose of these records is engineering validation, not final model training.



The subset should provide enough variation to expose problems in:



\- signal loading

\- channel handling

\- annotation parsing

\- sleep-stage conversion

\- event alignment

\- missing/undefined annotations

\- recording duration

\- physiological signal quality

\- different event distributions



The exact record IDs should be selected programmatically from the official training record list rather than manually guessed.



\---



\## 6. Selection Principle



Record selection should be deterministic and documented.



The initial selection process should:



1\. obtain the official training-record list;

2\. identify candidate records;

3\. select approximately 10 records;

4\. record their IDs and selection method;

5\. download only those records;

6\. verify every downloaded record;

7\. document any missing or malformed components.



Random selection may be used later for model-development subsets, but the initial engineering subset should remain reproducible.



\---



\## 7. Expected Local Structure



The recommended local structure is:



```text

S:\\Symbiont\\

│

├── Datasets\\

│   ├── raw\\

│   │   ├── sleep-edfx-1.0.0\\

│   │   └── physionet-challenge-2018\\

│   │       └── training\\

│   │           ├── <record-1>\\

│   │           ├── <record-2>\\

│   │           └── ...

│   │

│   └── processed\\

│       └── ...

│

├── docs\\

│   └── reconnaissance\\

│

└── research\\

&#x20;   └── reconnaissance\\

```



Raw downloaded dataset files remain outside normal Git tracking.



\---



\## 8. Storage Policy



Raw PhysioNet files must not be committed to the Git repository.



The repository should contain:



\- acquisition scripts

\- record-selection manifests

\- checksums where useful

\- processing code

\- documentation

\- audit results



The repository should not contain:



\- raw `.mat` signal files

\- raw `.hea` files when covered by the dataset policy

\- large raw physiological recordings

\- downloaded web snapshots

\- temporary reconnaissance artifacts



\---



\## 9. Acquisition Manifest



The initial subset should have a manifest containing at least:



| Field | Purpose |

|---|---|

| record\_id | PhysioNet record identifier |

| dataset | Dataset name/version |

| subset | Training/test |

| acquisition\_date | When downloaded |

| source | Official PhysioNet location |

| expected\_files | Files expected for the record |

| downloaded\_files | Files actually obtained |

| verification\_status | Download integrity result |

| notes | Exceptions or observations |



The manifest becomes the reproducible record of what data Symbiont actually used.



\---



\## 10. Integrity Verification



Every selected record must be verified after acquisition.



Verification should establish:



1\. expected files exist;

2\. files are readable;

3\. signal headers are valid;

4\. channel count is available;

5\. sampling frequency is available;

6\. signal duration is available;

7\. annotation files are readable;

8\. annotations correspond to the selected record;

9\. no unexpected truncation is detected.



Where official checksums are available, they should be preferred over informal file-size checks.



\---



\## 11. First Processing Gate



The first ten records are not yet intended for model training.



They are intended to answer:



> Can Symbiont reliably transform a real PhysioNet PSG record into a unified representation containing signals, sleep stages, physiological events, and temporal alignment?



The processing gate passes only when the pipeline can successfully perform this transformation on the selected development records.



\---



\## 12. Expansion Strategy



After the initial subset passes the processing gate:



```text

10 records

&#x20;   ↓

Pipeline validation

&#x20;   ↓

\~50 records

&#x20;   ↓

Model/prototype development

&#x20;   ↓

Larger training subset

&#x20;   ↓

Held-out evaluation

```



The exact expansion sizes will be decided using actual processing time, storage requirements, label distributions, and model requirements.



No arbitrary dataset size will be declared sufficient before measuring these factors.



\---



\## 13. Test Data Policy



The PhysioNet Challenge test set must not be treated as ordinary training data.



The initial development workflow should use training records with available annotations.



If the official test data does not expose the required labels, it must not be used to claim supervised performance.



Future evaluation strategy must distinguish:



\- development data

\- validation data

\- held-out evaluation data

\- official challenge test data, where applicable



\---



\## 14. Data Leakage Prevention



The acquisition and processing architecture must prevent information from evaluation records entering training.



Where records from the same subject or related recordings can be identified, subject-level separation should be preferred over naive random epoch splitting.



The exact grouping policy will be established once the dataset metadata and record structure are inspected programmatically.



\---



\## 15. Current Decision



\*\*Decision:\*\*



Begin with approximately \*\*10 PhysioNet Challenge 2018 training records\*\*.



Do not download the full dataset.



Do not train a model yet.



First prove that the complete data-to-representation pipeline works reproducibly.



\---



\## 16. Next Actions



The next implementation sequence is:



```text

1\. Obtain official training RECORDS list

&#x20;       ↓

2\. Programmatically select 10 records

&#x20;       ↓

3\. Save selection manifest

&#x20;       ↓

4\. Download required files only

&#x20;       ↓

5\. Verify downloaded records

&#x20;       ↓

6\. Build unified record loader

&#x20;       ↓

7\. Parse sleep-stage annotations

&#x20;       ↓

8\. Parse event/arousal annotations

&#x20;       ↓

9\. Verify sample alignment

&#x20;       ↓

10\. Produce first processed record

```



The acquisition phase is complete only after the selected records have passed integrity verification.



\---



\## 17. Decision Boundary



The project will not proceed to large-scale model training until the following statement can be demonstrated:



> Given a valid PhysioNet training record, Symbiont can reproducibly load its physiological signals, sleep-stage information, and event annotations into a consistent internal representation while preserving their temporal relationship.



This is the immediate engineering milestone.

