# Portal submission: Ratchet (contribution type 52)

## Title

```
Ratchet: evidence may contradict a milestone, never unlatch it
```

## Notes / description

```
Every consensus friendly use of a model so far answers one question once. Real agreements are a sequence, evidenced in pieces over time, by parties who are not disinterested. The obvious design is a boolean per milestone that the model sets on each new document, and it fails in one expensive way: evidence is reversible and payment is not. Money released when "delivered" turned true cannot be un-released when next week's document says it never happened.

Ratchet makes the state monotone. A publisher registers a plan of named stages, each declaring what it comes after, and a prerequisite must already be defined above it, which makes the plan a DAG by construction. A stage that latches stays latched. A later document denying it produces a retraction record next to it; the latch never moves. The evidence is allowed to contradict itself, the ledger is not allowed to pretend it did not.

The split is the design: the model reports, the contract ratchets. Validators only ever compare two sorted lists of names drawn from the published plan. Ordering, latching and retraction recording are ordinary deterministic code running after the call, against state every validator already shares, so there is nothing there to disagree about.

On Bradbury, one plan and two tracks. Four documents walked a shipment through picked up, customs cleared and delivered, then a correction notice denied the delivery. The chain shows delivered still latched and also retracted. Two consumer contracts then take opposite directions from the same track: the escrow paid 100 and 250 for clean stages and refused the contradicted 650 tranche, while a credit line drew 300, latched a default, and stayed permanently shut with 700 of its limit unusable. The whole guard is exposed as views with no model, so every rejection can be reproduced by anyone.
```

## Evidence links (the required minimum, two)

1. Repository: `https://github.com/0xyuura/genlayer-ratchet`
2. Contract on Bradbury: `https://explorer-bradbury.genlayer.com/address/0xbAa7965fbf042FB8acd55cc07EB0593413dB64Bd`

Everything else (Studio import link, consumer addresses, the full on chain
result tables, function names) lives in the README so the submission carries
only what it must.

## Addresses

| Contract | Address |
| --- | --- |
| Ratchet | 0xbAa7965fbf042FB8acd55cc07EB0593413dB64Bd |
| StagedEscrow | 0xBC8c0C929545BF17c615729Db5111968598B1e03 |
| BreachGate | 0x34A724A620cA363AF401b73a38bC85393c7680a6 |

Plan: `p2540d30418df852daf9a4f265742e188` (delivery_escrow).
Tracks: `t1` (shipment, with a retracted delivery), `t2` (defaulted).
