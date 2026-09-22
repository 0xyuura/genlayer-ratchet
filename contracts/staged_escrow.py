# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""StagedEscrow: pays a tranche per milestone, and only on clean progress.

It holds no model and no web access. It reads one Ratchet track, and for the
stage it was asked about it pays that stage's tranche once.

Two rules do the work. A tranche is paid only when the stage has latched, which
the ratchet guarantees is permanent, so the payment can never be justified by
a claim that is later withdrawn. And a tranche is refused when the stage
carries a retraction, because a milestone some document has since contradicted
is exactly the one not to send money against.

That second rule is why Ratchet records retractions instead of unlatching. An
unlatch would silently erase the reason to look; a recorded contradiction
leaves the decision to the party holding the money.
"""

import json
import typing
from genlayer import *

ERROR_EXPECTED = "[EXPECTED]"


def tranches_from_input(raw: typing.Any) -> list:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raise ValueError("TRANCHES_NOT_JSON")
    if not isinstance(raw, list) or not raw:
        raise ValueError("TRANCHES_SHAPE")
    out = []
    for value in raw:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError("TRANCHES_VALUE")
        out.append(value)
    return out


def plan_stage_index(plan: dict, stage: str) -> int:
    names = [s["name"] for s in plan["stages"]]
    if stage not in names:
        raise ValueError("UNKNOWN_STAGE")
    return names.index(stage)


def plan(track: dict, stage: str, tranches: list, index: int) -> int:
    """Read one track into exactly what this contract will pay for a stage."""
    if stage not in track.get("latched", []):
        raise ValueError("NOT_REACHED")
    if stage in track.get("retracted", []):
        raise ValueError("CONTRADICTED")
    if not 0 <= index < len(tranches):
        raise ValueError("STAGE_OUT_OF_TABLE")
    return tranches[index]


def same_subject(track: dict, sender: str) -> bool:
    return str(track.get("subject", "")).lower() == str(sender).lower()


def _fail(code: str) -> typing.NoReturn:
    raise gl.vm.UserError(ERROR_EXPECTED + " " + code)


class StagedEscrow(gl.Contract):
    ratchet: Address
    plan_id: str
    tranches: DynArray[u256]
    released: u256
    payments: DynArray[str]
    paid: TreeMap[str, str]

    def __init__(self, ratchet: typing.Any, plan_id: str,
                 tranches: typing.Any) -> None:
        self.ratchet = ratchet if isinstance(ratchet, Address) else Address(str(ratchet))
        self.plan_id = str(plan_id)
        try:
            table = tranches_from_input(tranches)
        except ValueError as err:
            _fail(str(err))
        published = json.loads(
            gl.get_contract_at(self.ratchet).view().get_plan(self.plan_id))
        # One tranche per stage, checked against the plan as published rather
        # than against what the deployer believed it published.
        if len(table) != len(published["stages"]):
            _fail("TRANCHES_LENGTH")
        for value in table:
            self.tranches.append(u256(value))
        self.released = u256(0)

    @gl.public.write
    def release(self, track_id: str, stage: str) -> None:
        tid, name = str(track_id), str(stage)
        key = tid + ":" + name
        if key in self.paid:
            _fail("ALREADY_RELEASED")
        track = json.loads(
            gl.get_contract_at(self.ratchet).view().get_track(tid))
        if str(track["plan_id"]) != str(self.plan_id):
            _fail("OTHER_PLAN")
        if not same_subject(track, str(gl.message.sender_address)):
            _fail("NOT_THE_SUBJECT")
        published = json.loads(
            gl.get_contract_at(self.ratchet).view().get_plan(self.plan_id))
        try:
            index = plan_stage_index(published, name)
            amount = plan(track, name, [int(t) for t in self.tranches], index)
        except ValueError as err:
            _fail(str(err))
        except Exception:
            _fail("TRACK_UNREADABLE")
        self.released = u256(int(self.released) + amount)
        self.payments.append(json.dumps({"track": tid, "stage": name,
                                         "amount": amount}, sort_keys=True))
        self.paid[key] = str(amount)

    @gl.public.view
    def status(self) -> str:
        return json.dumps({"plan_id": str(self.plan_id),
                           "released": int(self.released),
                           "tranches": [int(t) for t in self.tranches],
                           "payments": [str(p) for p in self.payments]},
                          sort_keys=True)
