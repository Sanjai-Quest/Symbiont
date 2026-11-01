# Symbiont - Dataset Reconnaissance Pass 1



**Project:** Symbiont  

**Phase:** Dataset Foundation  

**Activity:** Reconnaissance Pass 1  

**Dataset:** Sleep-EDF Expanded v1.0.0  

**Primary tool:** MNE-Python  

**MNE version:** 1.13.2  

**Status:** Completed



\---



## 1. Objective



The objective of Reconnaissance Pass 1 was to inspect the Sleep-EDF Expanded dataset before designing preprocessing or machine-learning pipelines.



The purpose was to establish:



\- What recordings are available.

\- How PSG and hypnogram files are paired.

\- How many records can be successfully read.

\- What channel configurations exist.

\- What sampling rates are present.

\- What sleep-stage annotations are present.

\- Whether the dataset can be systematically processed using MNE-Python.



No machine-learning model was trained during this phase.



\---



## 2. Dataset



Dataset used:



**Sleep-EDF Expanded Database v1.0.0**



Dataset location:



```text

S:\\Symbiont\\Datasets\\raw\\sleep-edfx-1.0.0\\sleep-edf-database-expanded-1.0.0

```



The dataset contains two main subsets:



```text

sleep-cassette

sleep-telemetry

```



Initial file inspection established:



\- Sleep-cassette: 306 EDF files

\- Sleep-telemetry: 88 EDF files

\- Total EDF files: 394

\- PSG/Hypnogram pairs: 197



A typical pair is:



```text

SC4001E0-PSG.edf

SC4001EC-Hypnogram.edf

```



The PSG file contains physiological recordings.



The hypnogram contains sleep-stage annotations.



\---



## 3. Tools



Python was used for dataset inspection.



MNE-Python was used to read EDF recordings and annotations.



MNE version:



```text

1.13.2

```



No raw dataset files were modified during reconnaissance.



\---



## 4. Initial Single-File PSG Inspection



A representative PSG file was inspected:



```text

SC4001E0-PSG.edf

```



The inspection established:



```text

Channels: 7

Sampling rate: 100.0 Hz

Duration: approximately 22.0833 hours

```



Channel names:



```text

EEG Fpz-Cz

EEG Pz-Oz

EOG horizontal

Resp oro-nasal

EMG submental

Temp rectal

Event marker

```



This confirmed that the dataset contains multiple physiological signal types rather than EEG alone.



\---



## 5. Initial Single-File Hypnogram Inspection



The corresponding hypnogram was inspected:



```text

SC4001EC-Hypnogram.edf

```



Results:



```text

Annotations: 154

Duration: 86400 seconds

```



Sleep-stage descriptions encountered:



```text

Sleep stage 1

Sleep stage 2

Sleep stage 3

Sleep stage 4

Sleep stage ?

Sleep stage R

Sleep stage W

```



The hypnogram therefore contains both sleep-stage labels and non-standard/unknown annotation categories that require further analysis.



The PSG and hypnogram durations were not assumed to be identical. The observed difference requires systematic dataset-wide alignment analysis in Reconnaissance Pass 2.



\---



## 6. Dataset-Wide Reconnaissance



A reconnaissance script was created at:



```text

S:\\Symbiont\\research\\reconnaissance\\dataset\_recon.py

```



The script:



1\. Located PSG files in both dataset subsets.

2\. Identified the corresponding hypnogram files.

3\. Loaded PSG files using MNE.

4\. Recorded channel counts.

5\. Recorded nominal sampling rates.

6\. Loaded hypnogram annotations.

7\. Recorded annotation counts and durations.

8\. Recorded unique sleep-stage descriptions.

9\. Assigned a processing status to each record.

10\. Wrote the reconnaissance results to a CSV file.



Output location:



```text

S:\\Symbiont\\research\\reconnaissance\\outputs\\dataset\_reconnaissance.csv

```



\---



## 7. Failed Attempt 1 - Sampling Rate Access



### Problem



The first version of the reconnaissance script attempted to access the sampling rate from individual channel dictionaries using:



```python

ch\["sfreq"]

```



This produced:



```text

KeyError('sfreq')

```



for the records.



### Cause



The expected `sfreq` field was not present in the individual channel dictionary being accessed.



### Resolution



The sampling rate was obtained from the MNE Raw object's information structure:



```python

raw.info\["sfreq"]

```



### Result



After correcting the sampling-rate access, the records could be inspected correctly.



\---



## 8. Failed Attempt 2 - Hypnogram Filename Assumption



### Problem



The first pairing logic assumed that the hypnogram filename could be generated directly from the PSG base filename.



This produced missing-hypnogram results even though the corresponding files existed.



### Cause



The dataset does not use one simple identical filename transformation for every record.



For example:



```text

PSG:

SC4001E0-PSG.edf



Hypnogram:

SC4001EC-Hypnogram.edf

```



The filename contains an additional character before the hypnogram suffix.



Hardcoding one filename transformation would therefore not be sufficiently robust.



### Resolution



The pairing logic was changed to dynamically search for the hypnogram using the shared filename prefix and the:



```text

\-Hypnogram.edf

```



suffix.



The script also checks for multiple candidates rather than silently choosing an arbitrary file.



### Result



The corrected pairing logic successfully identified the hypnogram for all 197 records.



\---



## 9. Final Reconnaissance Pass 1 Results



The corrected script produced:



```text

Status:

&#x20; OK: 197

```



Therefore:



```text

197 / 197 PSG-Hypnogram pairs successfully processed

```



### Channel counts



```text

5 channels: 44 records

7 channels: 153 records

```



### Sampling rates



```text

100.0 Hz: 197 records

```



### Sleep-stage presence



Record-level presence counts:



```text

Movement time: 59

Sleep stage 1: 197

Sleep stage 2: 197

Sleep stage 3: 178

Sleep stage 4: 118

Sleep stage ?: 150

Sleep stage R: 197

Sleep stage W: 197

```



These counts represent the number of records in which a category was encountered.



They are NOT epoch counts and do NOT represent the total amount of time spent in each stage.



\---



## 10. Interpretation



The first reconnaissance pass establishes several important properties of the dataset.



### 10.1 Complete pair discovery



All 197 PSG/Hypnogram pairs were successfully identified and read.



This indicates that the dataset is suitable for systematic programmatic processing using the current MNE-based approach.



### 10.2 Channel variability



The dataset contains two observed channel-count configurations:



```text

5 channels

7 channels

```



This means future preprocessing cannot blindly assume that every recording contains the same number of channels.



Channel availability must therefore be explicitly inspected before defining the final feature/input representation.



### 10.3 Sampling-rate consistency



All 197 records reported:



```text

100.0 Hz

```



This is useful for subsequent signal-processing design, although channel-specific details still need to be investigated.



### 10.4 Sleep-stage variability



Not every record contains every sleep-stage category.



In particular:



\- Stage 3 is present in 178 records.

\- Stage 4 is present in 118 records.

\- Unknown stage `?` is present in 150 records.

\- Movement time is present in 59 records.



These categories require more detailed duration and temporal analysis before deciding how labels should be handled.



### 10.5 PSG/Hypnogram alignment



A representative record showed:



```text

PSG duration: approximately 22.08 hours

Hypnogram coverage: 24 hours

```



This difference is not being classified as an error at this stage.



Systematic alignment analysis is required before determining whether the difference is expected, whether annotations extend beyond the usable PSG recording, or whether additional timing considerations are required.



\---



## 11. Important Limitations of Pass 1



Pass 1 does NOT establish:



\- Exact epoch counts.

\- Exact duration spent in each sleep stage.

\- Whether all annotations align with the PSG signal.

\- Whether annotation gaps exist.

\- Whether annotations overlap.

\- Whether annotations extend beyond the usable PSG recording.

\- Whether all sleep-stage annotations correspond to clean 30-second epochs.

\- The final label representation to be used by Symbiont.

\- The final preprocessing pipeline.



These questions are intentionally deferred to Reconnaissance Pass 2.



\---



## 12. Decision



Reconnaissance Pass 1 is considered complete.



The dataset is sufficiently understood to proceed to the next inspection stage.



No machine-learning architecture will be designed yet.



No training will begin yet.



The next activity is:



**Reconnaissance Pass 2 - PSG/Hypnogram Alignment and Stage-Duration Analysis**



\---



## 13. Next Step



Reconnaissance Pass 2 will investigate every record for:



1\. PSG duration.

2\. Hypnogram duration.

3\. Duration difference.

4\. Annotation count.

5\. 30-second epoch structure.

6\. Duration per sleep-stage category.

7\. Unknown-stage duration.

8\. Movement-time duration.

9\. Annotation gaps.

10\. Annotation overlaps.

11\. Annotation timing relative to PSG coverage.

12\. Unusual or potentially problematic records.



The results will be used to determine the actual preprocessing requirements for the Symbiont pipeline.



\---



## 14. Status



```text

Reconnaissance Pass 1: COMPLETE

Dataset pair discovery: COMPLETE

Basic channel inspection: COMPLETE

Sampling-rate inspection: COMPLETE

Basic annotation inspection: COMPLETE

PSG/Hypnogram alignment analysis: PENDING

Model development: NOT STARTED

```

