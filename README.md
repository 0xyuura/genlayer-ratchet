# Ratchet

**Published milestones that can only ever move forward. A later document can
contradict a stage; it can never unlatch one.**

Live on Testnet Bradbury at
[`0xbAa7965fbf042FB8acd55cc07EB0593413dB64Bd`](https://explorer-bradbury.genlayer.com/address/0xbAa7965fbf042FB8acd55cc07EB0593413dB64Bd).
Two unrelated consumer contracts act on real tracks; see
[Exercised on chain](#exercised-on-chain).

Call it without a local setup:
[open it in GenLayer Studio](https://studio.genlayer.com/?import-contract=0xbAa7965fbf042FB8acd55cc07EB0593413dB64Bd)

## The problem

Every other primitive of this kind answers one question once. Real agreements
are not like that. A shipment is picked up, then cleared, then delivered, and
the evidence arrives in pieces over days, written by parties with reasons to
shade it.

The obvious design is a boolean per milestone that the model sets each time it
reads a new document. That is a hole, not a design. Money released when
`delivered` turned true cannot be un-released when next week's document says it
was never delivered. A milestone that can flip back is a milestone that can be
used to rewrite history after the payment has already left.

## The move

State is monotone. A stage that latches stays latched, forever.

A later document that contradicts it does not unlatch anything. It is recorded
as a **retraction** against that stage, which is a first class fact a consumer
can refuse to pay on. The evidence is allowed to contradict itself; the ledger
is not allowed to pretend it did not.

The publisher also declares the order. A stage may only latch once every stage
it depends on has latched, so no document can deliver a parcel that was never
picked up, however it is worded.

## The split that makes it sound

**The model reports. The contract ratchets.**

| Step | Who | Compared by validators? |
| --- | --- | --- |
| Read the document, list stages reached and denied | model | yes, exactly |
| Names are real, no duplicates, none in both lists | code, inside the call | yes, exactly |
| Order constraints, latching, retraction recording | code, after the call | no, it is deterministic on shared state |

Validators only ever compare `{"reached": [...], "denied": [...]}`: two sorted
lists of names drawn from a closed published set. The entire state transition
is ordinary code running against ordinary on chain state that every validator
already holds, so there is nothing there to disagree about.

## A published plan

```json
{
  "name": "delivery_escrow",
  "stages": [
    {"name": "picked_up",       "after": []},
    {"name": "customs_cleared", "after": ["picked_up"]},
    {"name": "delivered",       "after": ["customs_cleared"]},
    {"name": "defaulted",       "after": []}
  ]
}
```

A prerequisite must already be defined above it. That one rule makes the plan a
DAG by construction, so there is no cycle check to get wrong and no plan can be
published that could never complete. The plan id is `p` plus the first 32 hex
characters of the sha256 of the canonical form, so changing an order constraint
makes a different plan and a consumer bound to an id keeps the rules it was
deployed against.

## What the model can and cannot do

| | |
| --- | --- |
| The model **can** | list stages the document says have happened, list stages it says have not, or say nothing about a stage |
| The model **cannot** | invent a stage, name one twice, put one in both lists, skip a prerequisite, or unlatch anything at all |

Leaving a stage out of both lists is the normal case and means the document did
not speak to it. Silence is not denial.

The full argument, failure classes and rejected alternatives are in
[docs/DESIGN.md](docs/DESIGN.md); the interface is in
[docs/INTEGRATING.md](docs/INTEGRATING.md).

## Quick start for a consuming contract

```python
track = json.loads(gl.get_contract_at(RATCHET).view().get_track(track_id))

if track["plan_id"] != MY_PLAN_ID:
    raise gl.vm.UserError("[EXPECTED] OTHER_PLAN")
if stage not in track["latched"]:
    raise gl.vm.UserError("[EXPECTED] NOT_REACHED")
if stage in track["retracted"]:          # decide this on purpose
    raise gl.vm.UserError("[EXPECTED] CONTRADICTED")
```

That third check is the one to think about, and the two consumers here answer
it deliberately differently.

## Exercised on chain

Three contracts on Testnet Bradbury, each byte identical to its file here:

| Contract | Address |
| --- | --- |
| `Ratchet` | [`0xbAa7965fbf042FB8acd55cc07EB0593413dB64Bd`](https://explorer-bradbury.genlayer.com/address/0xbAa7965fbf042FB8acd55cc07EB0593413dB64Bd) |
| `StagedEscrow` | [`0xBC8c0C929545BF17c615729Db5111968598B1e03`](https://explorer-bradbury.genlayer.com/address/0xBC8c0C929545BF17c615729Db5111968598B1e03) |
| `BreachGate` | [`0x34A724A620cA363AF401b73a38bC85393c7680a6`](https://explorer-bradbury.genlayer.com/address/0x34A724A620cA363AF401b73a38bC85393c7680a6) |

One published plan, `p2540d30418df852daf9a4f265742e188`, and two tracks.

Track `t1`, four documents read by live consensus:

| Document | Effect |
| --- | --- |
| carrier collected the consignment from the depot | latched `picked_up` |
| customs broker released it at 14:20 | latched `customs_cleared` |
| proof of delivery, signed for by the consignee | latched `delivered` |
| correction notice: the POD was filed against the wrong consignment, it was never delivered | **retracted** `delivered`, latched nothing |

The state after all four, read back from the chain:

```json
{"latched": ["customs_cleared", "delivered", "picked_up"],
 "retracted": ["delivered"], "observations": 4}
```

`delivered` is still latched. The ratchet did not run backwards. The
contradiction was recorded next to it instead, which the two views make
directly checkable:

| Call | Result |
| --- | --- |
| `has(t1, delivered)` | `true`, it did latch and always will have |
| `clean(t1, delivered)` | `false`, something has since contradicted it |
| `clean(t1, customs_cleared)` | `true`, uncontradicted progress |

Then the consumers, from the same track:

| Step | Result |
| --- | --- |
| `StagedEscrow.release(t1, picked_up)` | paid 100 |
| `StagedEscrow.release(t1, customs_cleared)` | paid 250, running total 350 |
| `StagedEscrow.release(t1, delivered)` | **refused**, total stays 350; the 650 tranche was never paid |
| `BreachGate.draw(300)` before any default | allowed, 300 drawn of a 1,000 limit |
| `observe(t2, notice of default)` | latched `defaulted` |
| `BreachGate.draw(300)` after | **refused**, `shut: true`, 700 of the limit left unusable |

The deterministic guard is visible to anyone through `check_report`, which
validates a report with no model, and `dry_run`, which additionally applies the
order rules against real track state:

| Call | Reply | Result |
| --- | --- | --- |
| `check_report` | `reached: [picked_up]` | `{"denied": [], "reached": ["picked_up"]}` |
| `check_report` | `reached: [teleported]` | `[EXPECTED] UNKNOWN_STAGE` |
| `check_report` | same stage reached and denied | `[EXPECTED] CONTRADICTORY_REPORT` |
| `check_report` | a stage listed twice | `[EXPECTED] REPORT_DUP` |
| `check_report` | an extra field | `[EXPECTED] REPORT_SHAPE` |
| `dry_run(t1)` | the whole chain at once | latches all three |
| `dry_run(t1)` | `delivered` with nothing before it | `[EXPECTED] OUT_OF_ORDER` |
| `dry_run(t1)` | `picked_up` and `delivered`, skipping customs | `[EXPECTED] OUT_OF_ORDER` |

```bash
genlayer call 0xbAa7965fbf042FB8acd55cc07EB0593413dB64Bd get_track --args t1
genlayer call 0xbAa7965fbf042FB8acd55cc07EB0593413dB64Bd clean --args t1 delivered
genlayer call 0xBC8c0C929545BF17c615729Db5111968598B1e03 status
genlayer call 0x34A724A620cA363AF401b73a38bC85393c7680a6 status
```

**What the chain taught.** Several observations ended with validators failing
to agree and nothing being stored, and had to be sent again. That is the right
failure: a document two honest readers read differently is one that should not
silently advance an escrow. It is also why the state transition sits outside
the model call. If the ratchet ran inside it, every retry would be reasoning
about state instead of about the document.

## Honest limitations

1. A latch is still the model's reading of a document. The plan bounds which
   stages exist and the order bounds when they may arrive; neither makes the
   document true.
2. Eight stages maximum, four prerequisites each. Plans past that are usually
   two plans.
3. There is no unlatch, by design, and therefore no way to correct a stage that
   latched on a document that was simply wrong. The retraction record exists so
   a consumer can decline to act; recovery is a matter for the parties.
4. `clean` is a convention, not a rule. Ratchet records the contradiction; each
   consumer decides whether it cares, and they should not all answer the same.
5. Documents and tracks are public, so the text should carry no secrets.

## Tests

```bash
python -m unittest discover -s tests     # 65 tests, offline, no model
```

The suite covers plan parsing and every rejection code, the report normaliser,
the agreement rule, the ratchet itself (ordering, chains in one document,
relatching as a no op, denial never unlatching), the prompt discipline and its
fence, and both consumers' rules. Three deliberate mutations, making the
ratchet two way, dropping the order check, and paying without consulting
retractions, all change behaviour the suite pins down, and the first of them
shows the credit gate reopening, which is the actual security failure.

## Layout

```
contracts/ratchet.py         the primitive, and every rule that votes
contracts/staged_escrow.py   consumer: pays per milestone, refuses contradicted ones
contracts/breach_gate.py     consumer: a credit line that shuts once and stays shut
tests/test_ratchet.py        the suite
docs/INTEGRATING.md          publish, track, observe, act
docs/DESIGN.md               claim, agreement, failure classes, limits
```

## Licence

MIT, see [LICENSE](LICENSE).
