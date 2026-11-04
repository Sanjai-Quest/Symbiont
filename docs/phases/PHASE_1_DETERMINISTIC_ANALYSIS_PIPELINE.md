# SYMBIONT



## Phase 1 - Deterministic Analysis Pipeline



**Project:** Symbiont  

**Phase:** 1  

**Phase name:** Deterministic Analysis Pipeline  

**Status:** IN PROGRESS  

**Previous phase:** Phase 0 - Dataset Feasibility, Product Definition \& Analysis Readiness  

**Primary dataset:** PhysioNet/CinC Challenge 2018 Sleep Arousal Detection



\---



## 1. Purpose



Phase 1 establishes the first reproducible analysis pipeline for Symbiont.



The purpose is to convert validated physiological recordings and their annotations into deterministic, interpretable measurements of sleep disruption.



No machine-learning model is introduced in this phase.



The pipeline must first prove that the underlying temporal relationships can be calculated correctly and reproducibly.



\---



## 2. Phase 1 Objective



The first analysis question is:



> After an annotated physiological event ends, how frequently does a scored arousal occur within defined temporal windows?



This measures temporal association.



It does not establish causation.



\---



## 3. Input Data



For each development record, the pipeline will use:



1\. PSG physiological signals

2\. Arousal target vector

3\. Sleep-stage masks

4\. WFDB event annotations



The development subset consists of the 10 validated PhysioNet records documented during Phase 0.



\---



## 4. Arousal Label Semantics



The arousal target uses:



\- `+1` = arousal region

\- `0` = scorable non-arousal region

\- `-1` = region that will not be scored



The `-1` regions must not be treated as negative training examples or as ordinary non-arousal regions.



\---



## 5. Event Representation



Annotated events are represented using sample indices.



Each event is treated as a half-open interval:



\[start, end)



The `start` sample is included.



The `end` sample is excluded.



This convention must remain consistent throughout the analysis.



\---



## 6. Sampling Rate



The PhysioNet development records are sampled at:



200 Hz



Therefore:



1 sample = 0.005 seconds



Temporal distances will be calculated from sample indices using the verified sampling frequency rather than assuming a fixed duration elsewhere in the code.



\---



## 7. Arousal Region Construction



Individual consecutive `+1` samples are not treated as separate arousals.



Contiguous `+1` samples must first be grouped into continuous arousal regions.



Example:



+1 +1 +1 +1 +1



represents one continuous arousal region.



This prevents artificial inflation of arousal counts.



\---



## 8. Temporal Relationships



For every physiological event, three relationships will be measured independently.



### 8.1 Event overlap



Determine whether a scored arousal occurs inside the event interval.



Example:



Event:

\[start ---------------- end]



Arousal:

&#x20;       \[---------]



Result:



overlap = TRUE



\---



### 8.2 Pre-event arousal



Determine whether a scored arousal occurred before the event.



The nearest preceding arousal region will be identified.



The temporal gap will be measured from the end of the preceding arousal region to the beginning of the event.



\---



### 8.3 Post-event arousal



Determine whether the nearest scored arousal begins after the event ends.



The event end is treated as time zero.



Example:



Event:

\[start ---------------- end]

&#x20;                           |

&#x20;                           0 seconds



Arousal:

&#x20;                             \[---------]



The gap is:



next\_arousal\_start - event\_end



converted from samples to seconds.



\---



## 9. Post-event Temporal Windows



Post-event arousal association will be measured using the following windows:



\- 0-5 seconds

\- >5-10 seconds

\- >10-20 seconds

\- >20-30 seconds

\- >30-60 seconds



A separate measurement will identify whether an arousal occurs within 60 seconds after the event.



The windows are mutually exclusive for the nearest qualifying post-event arousal.



\---



## Methodology Revision: Bounded Post-Event Attribution Window

### Reason for revision

The first implementation of the Phase 1 analysis searched for the next arousal region after each physiological event without applying a maximum temporal limit.

Diagnostic analysis on the validation record `tr03-0005` showed that this can produce biologically meaningless relationships. For example, one central apnea ended at approximately 16,374 seconds, while the next arousal region began approximately 7,623 seconds later. A gap of more than two hours cannot reasonably be treated as a post-event association.

Therefore, the unrestricted "next arousal" search is not suitable as an attribution metric.

### Revised rule

For Phase 1 post-event analysis:

> An arousal is considered temporally associated with an event after the event only when the arousal begins within 60 seconds of the event end.

Post-event windows are therefore:

- `0-5s`
- `>5-10s`
- `>10-20s`
- `>20-30s`
- `>30-60s`

If the next arousal begins more than 60 seconds after the event ends, the event is recorded as having:

`NO POST-EVENT ASSOCIATION`

The distant arousal may still exist in the recording, but it is not considered part of the Phase 1 event-attribution analysis.

### Important interpretation

The 60-second limit is an analytical boundary, not a causal boundary.

A post-event association does not demonstrate that the physiological event caused the arousal.

The purpose of this analysis is to measure temporal relationships between independently annotated events and arousals. Causal interpretation is outside the scope of Phase 1.

### Scope of the revision

This revision affects only the post-event proximity calculation.

The following remain independent analyses:

1. Direct event/arousal overlap.
2. Pre-event arousal proximity.
3. Post-event arousal proximity within the bounded 60-second window.

The existing post-event bins remain unchanged.

### Validation evidence

Validation record:

`tr03-0005`

The diagnostic analysis demonstrated both:

- meaningful post-event relationships occurring within tens of seconds, and
- distant "next arousal" relationships extending far beyond a meaningful attribution window.

This evidence justified replacing the unrestricted nearest-arousal search with a bounded 60-second analysis window.

### Status

**Methodology revision: APPROVED FOR IMPLEMENTATION**

The analysis implementation must now be updated to enforce the 60-second maximum before calculating post-event association windows.

## 10. Boundary Rules



All event and arousal intervals use half-open intervals.



For example:



\[start, end)



If an event ends at sample 22,000 and an arousal begins at sample 22,600:



gap = 22,600 - 22,000

gap = 600 samples



At 200 Hz:



gap = 600 / 200

gap = 3 seconds



Therefore the arousal belongs to the 0-5 second post-event window.



\---



## 11. Example Validation Cases



### Case A: Post-event arousal



Event:



\[20,000 ---------------- 22,000)



Arousal:



\[22,600 ---------------- 23,000)



Gap:



600 samples = 3 seconds



Expected:



\- overlap = FALSE

\- post 0-5s = TRUE

\- post 5-10s = FALSE

\- post 10-20s = FALSE

\- post 20-30s = FALSE

\- post 30-60s = FALSE



\---



### Case B: Overlapping arousal



Event:



\[20,000 ---------------- 22,000)



Arousal:



\[21,500 ---------------- 22,300)



Expected:



\- overlap = TRUE

\- post-event association = FALSE



The arousal is not classified as a post-event arousal because it begins before the event ends.



\---



### Case C: Pre-event arousal



Arousal:



\[18,800 ---------------- 19,600)



Event:



\[20,000 ---------------- 22,000)



Gap:



400 samples = 2 seconds



Expected:



\- overlap = FALSE

\- pre-event within 5s = TRUE

\- post-event association = FALSE



\---



### Case D: 60-second boundary



Event ends at:



22,000



Arousal begins at:



34,000



Gap:



12,000 samples = 60 seconds



Expected:



post-event within 60s = TRUE



An arousal beginning after 60 seconds is not included.



\---



## 12. Planned Output



For each event type, the pipeline will produce:



\- total event count

\- overlap count

\- overlap percentage

\- post-event 0-5 second count and percentage

\- post-event 5-10 second count and percentage

\- post-event 10-20 second count and percentage

\- post-event 20-30 second count and percentage

\- post-event 30-60 second count and percentage

\- post-event within-60-second count and percentage

\- pre-event temporal measurements



The analysis will also retain record-level results so that aggregate statistics do not hide large differences between individual recordings.



\---



## 13. Initial Event Types



The initial development analysis will operate on the event types successfully parsed during Phase 0:



\- `resp\_hypopnea`

\- `resp\_obstructiveapnea`

\- `resp\_centralapnea`

\- `resp\_mixedapnea`

\- `arousal\_rera`



This list represents the currently verified development-subset vocabulary.



It must not be interpreted as the complete event vocabulary of the entire PhysioNet dataset until a complete annotation-vocabulary audit is performed.



\---



## 14. Validation Strategy



The pipeline will not immediately be executed across all development records.



Validation sequence:



1\. Create the analysis implementation.

2\. Perform Python syntax validation.

3\. Review implementation against this methodology.

4\. Execute on one record only.

5\. Inspect the generated results.

6\. Compare selected results against raw annotations.

7\. Correct any methodological or implementation errors.

8\. Execute the validated pipeline across all 10 development records.

9\. Document the resulting measurements.



\---



## 15. Reproducibility Requirements



The pipeline must:



\- use deterministic calculations;

\- record the input record identifier;

\- record sampling frequency;

\- preserve sample-based timing;

\- distinguish excluded `-1` regions from valid `0` regions;

\- preserve event type information;

\- preserve record-level results;

\- avoid hard-coded physiological conclusions;

\- produce machine-readable output where practical.



\---



## 16. Interpretation Boundary



The results of this phase represent temporal association.



The analysis must not claim:



> Event X causes arousal.



Instead, results should be described as:



> Event X was temporally associated with a subsequent scored arousal within the specified window.



Further analysis will be required before determining whether the observed association is stronger than expected from background arousal frequency.



\---



## 17. Baseline Analysis



A later analysis should compare observed event-to-arousal proximity against an appropriate background arousal rate.



This is intentionally not part of the first implementation.



The first objective is to establish the raw temporal relationship correctly before introducing a baseline or statistical comparison.



\---



## 18. Phase 1 Completion Criteria



Phase 1 will not be considered complete until:



\- the deterministic pipeline executes successfully;

\- one-record validation passes;

\- the 10-record development analysis executes successfully;

\- outputs are reproducible;

\- boundary conditions are verified;

\- excluded labels are handled correctly;

\- results are documented;

\- no unsupported causal claims are made.



\---



## 19. Current Status



Phase 0 established dataset feasibility.



Phase 1 now begins with deterministic event-to-arousal temporal analysis.



The first implementation target is:



research/analysis/event\_arousal\_proximity.py



No machine-learning model will be introduced until this deterministic analysis layer has been validated.



\---



## 20. Phase 1 Starting Decision



**STATUS: IN PROGRESS**



**FIRST IMPLEMENTATION: Event-to-Arousal Temporal Proximity Analysis**



**VALIDATION RECORD: tr03-0005**



**DEVELOPMENT SET: 10 validated records**


