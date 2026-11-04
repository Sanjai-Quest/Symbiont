
SYMBIONT — PHASE 1
Baseline and Control Methodology
Status: Methodology Definition  

Phase: Phase 1 — Deterministic Analysis Pipeline  

Purpose: Establish whether observed post-event arousal associations exceed a comparable background rate.

1. Purpose
The preceding Phase 1 analysis measured how frequently an annotated physiological event is followed by a scored arousal within 60 seconds.

Across the fixed 10-record development subset:

Total annotated events: 1,362

Direct event/arousal overlap: 301

Events followed by an arousal within 60 seconds: 156

These measurements are descriptive.

They do not establish that physiological events are associated with arousals more frequently than would occur naturally because arousals already occur throughout sleep.

Therefore, the next analysis introduces a comparable non-event control condition.

2. Null and Alternative Hypotheses
Null hypothesis — H0
Annotated physiological events are not followed by scored arousals more frequently than comparable non-event control windows.

Alternative hypothesis — H1
Annotated physiological events are followed by scored arousals more frequently within 60 seconds than comparable non-event control windows.

The analysis is designed to test temporal association, not causation.

3. Observed Event Condition
For every parsed physiological event:

Identify the event interval [start, end).

Identify the event end time.

Search for the next scored arousal region.

Measure the time between event end and arousal onset.

Record an association when the arousal begins within 60 seconds after event end.

The existing Phase 1 definitions remain unchanged.

The post-event windows are:

0–5 seconds

5–10 seconds

10–20 seconds

20–30 seconds

30–60 seconds

4. Control Condition
A control window represents a comparable point in the same recording where the selected physiological event is absent.

The control condition must satisfy the same general observation requirements as an event window.

A control point must:

belong to the same recording;

occur within the usable PSG recording boundary;

have sufficient recording remaining for the complete 60-second observation period;

not be inside an excluded -1 region;

not overlap an annotated physiological event;

not overlap a scored arousal at the control starting point;

have a valid sleep-stage context where stage matching is possible.

The control must therefore represent a plausible non-event comparison rather than an arbitrary timestamp.

5. Sleep-Stage Matching
Arousal frequency is not assumed to be uniform across sleep stages.

Therefore, control selection should preferentially match the sleep-stage context of the corresponding observed event.

The initial matching principle is:

> An event should be compared with control windows occurring in the same recording and, where valid stage information exists, within the same sleep-stage category.

The supported stage categories are:

Wake

N1

N2

N3

REM

Undefined or excluded sleep-stage regions must not be silently converted into valid stage labels.

6. Event Contamination Rule
A control window must not contain another annotated physiological event.

This prevents the control condition from becoming an unrecognized event condition.

For a 60-second control observation window:


control_start → control_start + 60 seconds
the interval must not intersect an annotated event.

The control must also remain within the valid recording boundary.

7. Arousal Measurement
The same arousal definition used in the observed event analysis must be used for controls.

A scored arousal is represented by the target label:


+1 = arousal
The following remain unchanged:


0  = scorable non-arousal

-1 = excluded / not scored
The -1 state must never be treated as a negative arousal label.

8. Control Sampling Strategy
The initial development analysis will use matched non-event control windows from the same records.

Controls should be selected using deterministic rules so that repeated execution produces the same control set.

Random control selection without a fixed seed is prohibited for the reproducible baseline analysis.

The first implementation should therefore record:

record identifier;

control start position;

sleep-stage category;

whether an arousal occurred within 60 seconds;

selected control index;

eligibility status.

9. Primary Metrics
The primary comparison will calculate:

Event association rate

event association rate =

events followed by arousal within 60s

/

eligible events
Control association rate

control association rate =

control windows followed by arousal within 60s

/

eligible control windows
Absolute difference

event rate − control rate
Relative enrichment

event rate / control rate
The relative enrichment metric must not be calculated when the control rate is zero without explicitly handling the undefined or infinite case.

10. Event-Type Analysis
The comparison should be calculated separately for each supported event type:

resp_hypopnea

resp_obstructiveapnea

resp_centralapnea

resp_mixedapnea

arousal_rera

RERA requires special interpretation because its annotation semantics are directly related to arousal-related respiratory events.

Therefore, RERA results must not be interpreted as independent evidence that respiratory events generally cause arousals.

11. Temporal Window Analysis
The baseline comparison should also be performed for the predefined temporal windows:

0–5 seconds

5–10 seconds

10–20 seconds

20–30 seconds

30–60 seconds

This allows the analysis to determine whether any observed enrichment is concentrated near the event or appears broadly throughout the 60-second period.

12. Record-Level Analysis
Aggregate rates alone are insufficient.

The analysis must also report results by individual record.

This is necessary because the current development subset already demonstrates substantial variation between records in:

event frequency;

arousal frequency;

excluded label proportion;

sleep duration;

event composition.

A relationship observed in only one or two recordings must not be presented as a general dataset-level pattern.

13. Multiple Events and Temporal Dependence
Sleep events and arousals are temporally clustered.

Therefore, individual event observations cannot automatically be assumed to be statistically independent.

The analysis must report the number of observations and should preserve record-level structure when evaluating uncertainty.

No statistical test will be selected solely because it produces a convenient p-value.

The statistical method must follow the structure of the control design.

14. Boundary Conditions
The following rules apply:

Event near recording end
If fewer than 60 seconds remain after the event end, the event may not have a complete observation window.

It must therefore be marked as ineligible for the primary 60-second comparison rather than silently treating missing time as no arousal.

Control near recording end
Controls must also have the full 60-second observation window available.

Excluded regions
A control must not begin inside an excluded -1 region.

If the observation window enters an excluded region, the control should be treated according to the final eligibility rule implemented by the analysis.

This rule must be explicitly recorded before final analysis.

15. No Causal Interpretation
The baseline analysis evaluates temporal association and enrichment.

It does not establish:

causation;

physiological mechanism;

clinical diagnosis;

patient-specific disease;

treatment recommendation.

For example:

> "Events were followed by arousals more frequently than matched control windows."

is an acceptable descriptive finding.

The following is not justified by this analysis:

> "The event caused the arousal."

16. Validation Strategy
The baseline implementation must be validated in stages.

Stage 1 — Syntax validation

python -m py_compile research\analysis\phase1_baseline_control.py
Stage 2 — Single-record validation
Use:


training/tr03-0005/tr03-0005
Verify:

event count;

control eligibility;

control count;

sleep-stage assignment;

event exclusion;

arousal detection;

60-second boundary handling.

Stage 3 — Manual inspection
Inspect several selected event and control windows against the underlying labels.

At least one example should represent:

an event followed by an arousal;

an event without a qualifying post-event arousal;

a control followed by an arousal;

a control without a qualifying post-event arousal.

Stage 4 — Fixed 10-record development subset
Run the analysis against the same deterministic 10-record manifest used throughout Phase 1.

No additional records should be introduced during this validation stage.

17. Reproducibility Requirements
The analysis must produce deterministic results.

The implementation must record:

dataset version;

development manifest;

analysis script;

control-selection rule;

sampling seed if applicable;

sleep-stage matching rule;

event exclusion rule;

arousal definition;

temporal window definitions;

output metrics.

Changing any of these methodological components requires a documented revision.

18. Interpretation Gate
The baseline analysis produces a decision point.

If event association is not meaningfully higher than control association
The current event-attribution hypothesis is weakened.

The product direction must be reconsidered before model development.

If event association is consistently higher than control association
The result provides evidence supporting further investigation of temporal event/arousal relationships.

It does not establish causation.

Further validation would then be justified.

19. Current Evidence
Before baseline analysis:


Development records:       10

Annotated events:       1,362

Direct overlap:           301

Post-event ≤60s:          156
These values are the observed-condition results.

They must not be interpreted as evidence of enrichment until the control condition has been evaluated.

20. Completion Criteria
This methodology stage is complete when:

control rules are explicitly defined;

the control-selection procedure is deterministic;

event and control eligibility are implemented;

sleep-stage matching is implemented or explicitly documented as unavailable;

single-record validation passes;

manual validation passes;

the fixed 10-record analysis completes;

event and control rates are reported;

record-level results are available;

no causal claims are made.

Status: Methodology defined. Implementation pending.

