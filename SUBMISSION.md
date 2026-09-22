# Portal submission: Ratchet (contribution type 52)

## Title

```
Ratchet: evidence may contradict a milestone, never unlatch it
```

## Notes / description

The Portal caps this field at 1000 characters.

```
Primitives of this kind answer one question once. Real agreements arrive in pieces over time. A boolean per milestone that the model resets on each document fails in one expensive way: evidence is reversible and payment is not. Money released when delivered turned true cannot be un-released when a later document denies it.

Ratchet makes state monotone. Stages declare what they come after, so a plan is a DAG by construction. A latched stage stays latched; a denial records a retraction beside it, never moving the latch.

The model reports, the contract ratchets: validators compare two sorted lists of published stage names, and ordering and latching run afterwards on shared state.

On Bradbury, four documents walked a shipment to delivered, then a correction denied it: it reads latched and retracted. One consumer paid the clean stages and refused the contradicted tranche; another latched a default and stayed shut.
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
