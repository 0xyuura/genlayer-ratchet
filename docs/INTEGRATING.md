# Integrating Ratchet

Four steps: publish a plan, open a track, observe documents, act on the state.

## 1. Publish a plan

Stages in order, each declaring what it comes after. A prerequisite must
already appear above it.

```bash
genlayer write 0xbAa7965fbf042FB8acd55cc07EB0593413dB64Bd publish --args \
  '{"name":"delivery_escrow","stages":[
     {"name":"picked_up","after":[]},
     {"name":"customs_cleared","after":["picked_up"]},
     {"name":"delivered","after":["customs_cleared"]},
     {"name":"defaulted","after":[]}]}'
```

Returns a plan id such as `p2540d30418df852daf9a4f265742e188`. Publishing is
idempotent. `plan_id_for` computes the id as a view, with no transaction, which
is the cheap way to confirm that what you are about to deploy against is what
you think it is.

Rejections happen here rather than later: `PLAN_KEYS`, `PLAN_NAME`,
`PLAN_STAGES`, `STAGE_KEYS`, `STAGE_NAME`, `STAGE_DUP`, `AFTER_SHAPE`,
`AFTER_DUP`, `AFTER_UNKNOWN`.

## 2. Open a track

A track is one agreement following one plan.

```bash
genlayer write 0xbAa7965fbf042FB8acd55cc07EB0593413dB64Bd open_track \
  --args p2540d30418df852daf9a4f265742e188
```

Returns a track id such as `t1`. The caller becomes the track's subject, and
both consumers here require the subject to be the one acting.

## 3. Observe a document

```bash
genlayer write 0xbAa7965fbf042FB8acd55cc07EB0593413dB64Bd observe --args t1 \
  "Proof of delivery: consignment DE-4471 was delivered at 09:05 and signed for."
```

Returns what changed:

```json
{"latched": ["delivered"], "retracted": [], "ignored": []}
```

| Field | Meaning |
| --- | --- |
| `latched` | stages that became true for the first time |
| `retracted` | latched stages this document denied; the latch is unchanged |
| `ignored` | stages the document reported that were already latched |

Send documents one at a time, in any order they arrive. A document that
evidences several stages at once latches all of them, provided the chain is
complete.

The transaction fails and stores nothing when the text is empty or oversized,
the track is unknown, the order rules are broken, the model answers with
something that is not two lists of known stage names, or validators do not
agree. Treat a failed observation as normal and send it again.

## 4. Act on the state

```python
track = json.loads(gl.get_contract_at(RATCHET).view().get_track(track_id))

if track["plan_id"] != MY_PLAN_ID:
    raise gl.vm.UserError("[EXPECTED] OTHER_PLAN")
if stage not in track["latched"]:
    raise gl.vm.UserError("[EXPECTED] NOT_REACHED")
if stage in track["retracted"]:
    raise gl.vm.UserError("[EXPECTED] CONTRADICTED")   # your call, see below
```

That last line is the decision the primitive deliberately does not make for
you. Which way it goes follows from which side of the trade you are on:

| Consumer | Side | On a retraction |
| --- | --- | --- |
| `StagedEscrow` | pays out | refuse; uncertainty costs the claimant a tranche |
| `BreachGate` | shuts off | ignore it; a gate that reopens can be reopened to order |

A consumer that closes on a signal must not reopen on the absence of one.

## Views

| View | Returns |
| --- | --- |
| `get_track(track_id)` | plan id, subject, latched, retracted, observation count |
| `has(track_id, stage)` | latched at all |
| `clean(track_id, stage)` | latched and never contradicted. What a payer should ask |
| `ready(track_id, stage)` | every prerequisite of `stage` has latched |
| `history(track_id)` | every observation and what it changed |
| `check_report(plan_id, report)` | validate a report with no model |
| `dry_run(track_id, report)` | what a report would do to a track, without doing it |
| `get_plan(plan_id)` | the canonical plan as stored |
| `counts()` | plans, tracks, observations |

`dry_run` is the one to reach for while designing a plan. It applies the order
rules against real state, so it tells you whether the sequence you expect is
actually expressible.

## Error codes

`[EXPECTED] <CODE>` from publishing, observing and views: the `PLAN_*`,
`STAGE_*` and `AFTER_*` codes above, plus `NO_SUCH_PLAN`, `NO_SUCH_TRACK`,
`TEXT_TYPE`, `TEXT_LENGTH`, `UNKNOWN_STAGE`, `OUT_OF_ORDER`.

`[LLM_ERROR] <CODE>` never stores anything: `REPORT_SHAPE`, `REPORT_DUP`,
`UNKNOWN_STAGE`, `CONTRADICTORY_REPORT`, `FENCE_COLLISION`.

## Designing a plan

- Name stages after events a document would actually assert, not after internal
  states. `customs_cleared` appears on a broker notice; `in_progress` does not.
- Only add an order constraint you would enforce against a real counterparty.
  Every constraint is a way for a legitimate document to be rejected.
- Terminal bad outcomes like `defaulted` usually have no prerequisites, so they
  can latch whenever the evidence arrives.
- Keep the stages few. Two stages a model could confuse is worse than one stage
  that covers both.
