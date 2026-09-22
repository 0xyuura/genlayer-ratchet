# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""BreachGate: a credit line that stays open until one stage latches.

It holds no model and no web access. It watches one Ratchet track and allows
draws against a limit until the stage it watches has latched, after which every
further draw is refused, permanently.

This is the mirror of StagedEscrow and the reason the ratchet has to be one
way. StagedEscrow refuses a contradicted milestone, so a retraction costs the
claimant a payment. Here a retraction changes nothing at all: once a default
has been recorded the line stays shut, because a gate that reopened on a later
document would hand the borrower the job of producing that document.

A consumer that closes on a signal must not reopen on the absence of one.

Whether the gate is shut is never stored. It is read from the track every time,
because a flag set on the way to a revert is a flag that is never written: the
failure rolls the transaction back, and the contract would report itself open
while refusing every draw.
"""

import json
import typing
from genlayer import *

ERROR_EXPECTED = "[EXPECTED]"


def allowed(track: dict, watch: str, amount: int, drawn: int,
            limit: int) -> int:
    """How much of a requested draw this contract will allow."""
    if amount <= 0:
        raise ValueError("AMOUNT")
    if watch in track.get("latched", []):
        raise ValueError("GATE_CLOSED")
    if drawn + amount > limit:
        raise ValueError("OVER_LIMIT")
    return amount


def same_subject(track: dict, sender: str) -> bool:
    return str(track.get("subject", "")).lower() == str(sender).lower()


def _fail(code: str) -> typing.NoReturn:
    raise gl.vm.UserError(ERROR_EXPECTED + " " + code)


class BreachGate(gl.Contract):
    ratchet: Address
    track_id: str
    watch: str
    limit: u256
    drawn: u256
    draws: DynArray[str]

    def __init__(self, ratchet: typing.Any, track_id: str, watch: str,
                 limit: typing.Any) -> None:
        self.ratchet = ratchet if isinstance(ratchet, Address) else Address(str(ratchet))
        self.track_id = str(track_id)
        self.watch = str(watch)
        track = json.loads(
            gl.get_contract_at(self.ratchet).view().get_track(self.track_id))
        published = json.loads(
            gl.get_contract_at(self.ratchet).view().get_plan(str(track["plan_id"])))
        names = [s["name"] for s in published["stages"]]
        # The watched stage must exist in the plan as published, or the gate
        # would be waiting for something that can never happen and would stay
        # open forever while appearing to be guarded.
        if self.watch not in names:
            _fail("WATCH_NOT_IN_PLAN")
        self.limit = u256(int(limit))
        self.drawn = u256(0)

    def _track(self) -> dict:
        return json.loads(
            gl.get_contract_at(self.ratchet).view().get_track(str(self.track_id)))

    @gl.public.write
    def draw(self, amount: typing.Any) -> None:
        track = self._track()
        if not same_subject(track, str(gl.message.sender_address)):
            _fail("NOT_THE_SUBJECT")
        try:
            taken = allowed(track, str(self.watch), int(amount),
                            int(self.drawn), int(self.limit))
        except ValueError as err:
            _fail(str(err))
        except Exception:
            _fail("TRACK_UNREADABLE")
        self.drawn = u256(int(self.drawn) + taken)
        self.draws.append(json.dumps({"amount": taken}, sort_keys=True))

    @gl.public.view
    def status(self) -> str:
        track = self._track()
        return json.dumps({"track_id": str(self.track_id),
                           "watch": str(self.watch),
                           "limit": int(self.limit),
                           "drawn": int(self.drawn),
                           "shut": str(self.watch) in track.get("latched", []),
                           "draws": [str(d) for d in self.draws]},
                          sort_keys=True)
