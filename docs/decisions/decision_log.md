Symbiont Decision Log
Decision 001 - PSG recording boundary is the physiological validity boundary
Date: 2026-11-01
Phase: Dataset reconnaissance, Pass 2
Status: Accepted

Decision
Use the actual PSG recording boundary as the valid physiological signal boundary. Do not assume that the hypnogram duration equals the available PSG duration.

Evidence
Across 197 records, PSG and hypnogram durations were not uniformly equal. 159 records contained annotations extending beyond the PSG boundary. Targeted inspection showed that cassette hypnogram periods after PSG termination can be represented as Sleep stage ? through the 24-hour annotation boundary.

Implementation consequence
A preprocessing epoch is eligible only when its full interval is contained within the PSG recording.

Decision 002 - Exclude unknown and movement labels from supervised targets
Date: 2026-11-01
Phase: Dataset reconnaissance, Pass 2
Status: Accepted for preprocessing

Decision
Treat Sleep stage ? as unscored/unknown and Movement time as non-sleep-target annotations. They will be excluded from supervised sleep-stage targets during preprocessing.

Important constraint
The raw labels remain preserved in reconnaissance outputs. No modification is made to the original dataset.

Decision 003 - Preserve raw Stage 3 and Stage 4 during reconnaissance
Date: 2026-11-01
Phase: Dataset reconnaissance, Pass 2
Status: Accepted

Decision
Do not merge Sleep stage 3 and Sleep stage 4 during raw-data reconnaissance.

Later normalization
During preprocessing:

Sleep stage 3 -> N3
Sleep stage 4 -> N3
Reason
Keeping the original labels during reconnaissance preserves traceability. The Stage 3/4 merge is a preprocessing transformation and must be separately documented.

Decision 004 - Exact 30-second epoch boundary definition
Date: 2026-11-01
Phase: Dataset reconnaissance, Pass 2B
Status: Accepted

Decision
The PSG end boundary is calculated as:

psg\_end = raw.times\[-1] + (1 / raw.info\["sfreq"])
An exact 30-second annotation is considered fully contained when its onset is non-negative and its end does not exceed psg\_end.

Validation
The corrected implementation produced:

10,258 exact 30-second annotations fully inside PSG
The independent stage-level aggregation also produced 10,258, giving a difference of zero.

Prior error
The earlier implementation used raw.times\[-1] as the recording boundary and incorrectly excluded the final 30-second annotation of SC4092E0.
