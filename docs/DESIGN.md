# Ratchet design

## Claim

Once the network has agreed a stage was reached, no later document, however
worded and whoever wrote it, can cause the contract to report that stage as not
reached. A contradicting document is recorded, never applied.

## The problem this exists for

The other primitives of this kind answer one question once. Agreements are not
one question. They are a sequence, evidenced in pieces, over time, by parties
who are not disinterested.

The obvious way to model that is a boolean per milestone that the model sets on
each new document. It fails in one specific and expensive way: payment is not
reversible and evidence is. Money released when `delivered` turned true cannot
be un-released when next week's document says it never happened. A milestone
that flips both ways is a lever for rewriting the past after the money has
moved, and the party best placed to pull it is the one who owes.

## The ratchet

A stage that latches stays latched.

A document that denies a latched stage produces a **retraction record** against
it. The latch does not move. Nothing is deleted. A consumer reading the track
sees both facts at once: this stage was reached, and something has since said
it was not.

This is the right shape because it separates two questions that a boolean
conflates. "Did the network ever agree this happened" is history and must be
immutable. "Should I act on it today" is a judgement and belongs to whoever is
about to part with something.

## The split: the model reports, the contract ratchets

| Step | Runs | Compared by validators |
| --- | --- | --- |
| Read the document, list stages reached and denied | inside the nondet call | yes, exactly |
| Names known, no duplicates, none in both lists | inside the nondet call | yes, exactly |
| Order constraints | after, on shared state | no |
| Latching, retraction recording, logging | after, on shared state | no |

Validators compare `{"reached": [...], "denied": [...]}`, two sorted lists of
names from a closed published set. Nothing else crosses the consensus boundary.

Keeping the state transition outside the call is not tidiness. Prior state is
already identical for every validator, so putting the transition inside would
add a second thing to disagree about while adding no information. It also means
a retry after a failed round reasons about the document again, not about a
state that may have moved.

## Order is published, not inferred

Each stage declares the stages it comes after, and a prerequisite must already
be defined above it in the list. That single rule makes the plan a DAG by
construction: no cycle can be written, so there is no cycle detection to get
wrong and no plan can be published that could never complete.

A stage may latch when its prerequisites are already latched **or** are
delivered by the same document, so one proof of delivery may legitimately carry
a whole chain. It may not skip a link, so a document cannot deliver a parcel
that was never collected.

## Agreement

Both lists are sorted, so two validators whose models emit the same stages in a
different order agree. Both lists are compared, so a document that denies
something is not interchangeable with one that is merely silent about it.

Saying a stage both happened and did not happen is not uncertainty, it is a
broken answer, and picking which half to keep would be inventing one. It fails
as a model error and nothing is stored.

## Silence is not denial

A stage absent from both lists means the document did not speak to it. This
matters more than it looks. If absence meant denial, every partial document
would retract everything it did not mention, and the retraction record would
carry no information at all.

## Choosing what a retraction means

Ratchet records the contradiction and stops. What to do about it depends
entirely on which way the consumer faces, and the two here are opposites on
purpose.

`StagedEscrow` pays out, so it refuses a contradicted stage: uncertainty costs
the claimant a tranche, and the money stays where it is until the parties sort
it out.

`BreachGate` shuts on a signal, so it ignores retractions completely. A gate
that reopened on a later document would hand the borrower the job of producing
that document. **A consumer that closes on a signal must not reopen on the
absence of one.**

Neither policy is correct in general. Both are stated in public, once, before
any document arrives.

## Prompt injection

The document is written by an interested party, so it is hostile by default. It
is fenced with a tag derived from the sha256 of the text and the canonical
plan, so it cannot contain its own fence, and a collision is refused.

The structural defence matters more. A successful injection can only move the
model to a different subset of published stage names. It is then measured
against the order constraints, and it can never unlatch anything, because
nothing in the system can. The worst an attacker achieves is a stage latching
early, which the order rules constrain and which the retraction record makes
visible to everyone afterwards.

## Failure classes

| Class | Example | Result |
| --- | --- | --- |
| Progress | document evidences the next stage | stage latches, permanently |
| Chained progress | one document evidences several stages | all latch, if the order holds |
| Contradiction | a later document denies a latched stage | retraction recorded, latch unmoved |
| Silence | document says nothing about a stage | nothing happens to it |
| Out of order | a stage whose prerequisites are missing | transaction fails, nothing stored |
| Model error | invented stage, duplicate, or a stage in both lists | transaction fails, nothing stored |
| Honest disagreement | validators read the document differently | no agreement, nothing stored |

The last two are features. A document two honest readers read differently
should not silently advance an escrow.

## Limits

1. **A latch is still the model's reading of a document.** The plan bounds
   which stages exist and the order bounds when they may arrive. Neither makes
   the document true.
2. **Eight stages, four prerequisites each.** Bigger plans are usually two
   plans, and every extra stage is another name for a model to confuse.
3. **There is no unlatch**, which is the point, and therefore no correction
   path for a stage that latched on a document that was simply wrong. The
   retraction record exists so a consumer can decline to act. Recovery is a
   matter for the parties, not for the ledger.
4. **`clean` is a convention.** Ratchet records; consumers decide. They should
   not all decide the same way.
5. **One track, one plan.** Amending a plan makes a different plan id, and
   existing tracks keep the rules they were opened under.

## Rejected alternatives

- **A boolean per stage the model sets each time.** The design this exists to
  replace. Reversible evidence, irreversible payment.
- **Unlatch on denial, and rely on consumers to be careful.** This deletes the
  only record that the evidence ever conflicted, which is precisely the fact
  worth keeping, and makes the safe consumer the one that saved its own copy.
- **Require a quorum of documents before latching.** Plausible, and it belongs
  in the consumer. Building it into the primitive would force one threshold on
  every user of it, and the right threshold for a 200 dollar parcel is not the
  right one for a shipping container.
- **Let the model see the whole document history each time.** Costly, and it
  makes every observation depend on every earlier one, so one disputed
  document poisons everything after it. Each document is read on its own; the
  ordering rules do the accumulating.
- **Infer the order from the stage list instead of publishing it.** Then the
  order is whatever the model believes today, which is the thing the whole
  design is trying not to depend on.
