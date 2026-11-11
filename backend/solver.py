"""Shift assignment in plain Python: no DB, so it can be tested on its own for now."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


# ---------- Input and Output ----------
@dataclass(frozen=True)
class MemberIn:
    id: int
    name: str
    points: int = 0  # Points season balance from the books/ledger


@dataclass(frozen=True)
class ShiftIn:
    id: int
    starts_at: datetime
    ends_at: datetime
    weight: int
    slots: int


@dataclass
class Problem:
    members: list[MemberIn]
    shifts: list[ShiftIn]
    available: set[tuple[int, int]]  # (member_id, shift_id) pairs
    # Shifts members already hold from earlier publishes: they count for overlaps and load.
    already_assigned: dict[int, list[ShiftIn]] = field(default_factory=dict)


Reason = Literal["already_on_shift", "busy_at_that_time"]


@dataclass
class Result:
    assignments: list[tuple[int, int]] = field(default_factory=list)  # (shift_id, member_id)
    unfilled: dict[int, int] = field(default_factory=dict)  # shift_id -> empty slots
    # For each shift with empty slots: who said yes, and why they couldn't take it.
    # An empty list means nobody said yes.
    blocked: dict[int, list[tuple[int, Reason]]] = field(default_factory=dict)


@dataclass
class State:
    """What has been decided so far during one solve."""

    shifts_of: dict[int, list[ShiftIn]]  # member_id -> shifts assigned so far
    load: dict[int, int]  # member_id -> weight taken on this round


# ---------- Hard rules: each one answers "may this member take this shift now?" ----------
Rule = Callable[[MemberIn, ShiftIn, Problem, State], bool]


def is_available(member: MemberIn, shift: ShiftIn, problem: Problem, state: State) -> bool:
    return (member.id, shift.id) in problem.available


def not_already_on_shift(member: MemberIn, shift: ShiftIn, problem: Problem, state: State) -> bool:
    return all(taken.id != shift.id for taken in state.shifts_of[member.id])


def no_overlap(member: MemberIn, shift: ShiftIn, problem: Problem, state: State) -> bool:
    return all(
        shift.ends_at <= taken.starts_at or taken.ends_at <= shift.starts_at
        for taken in state.shifts_of[member.id]
    )


HARD_RULES: list[Rule] = [is_available, not_already_on_shift, no_overlap]

# What to tell the coordinator when a member who said yes is stopped by a rule.
REASONS: dict[Rule, Reason] = {
    not_already_on_shift: "already_on_shift",
    no_overlap: "busy_at_that_time",
}


def blocking_reason(
    member: MemberIn, shift: ShiftIn, problem: Problem, state: State, rules: list[Rule]
) -> Reason | None:
    """Why a member who said yes can't take this shift, or None if they can."""
    for rule in rules:
        if rule is not is_available and not rule(member, shift, problem, state):
            return REASONS[rule]
    return None


# ---------- Greedy solver ----------
def fairness_score(member: MemberIn, state: State) -> tuple[int, int]:
    """Lower goes first: points already earned plus load taken on this round.
    The member id breaks ties, so the result is always the same for the same input."""
    return (member.points + state.load[member.id], member.id)


def candidate_count(shift: ShiftIn, problem: Problem) -> int:
    return sum(1 for m in problem.members if (m.id, shift.id) in problem.available)


def solve_greedy(problem: Problem, rules: list[Rule] = HARD_RULES) -> Result:
    state = State(
        shifts_of={m.id: list(problem.already_assigned.get(m.id, [])) for m in problem.members},
        load={
            m.id: sum(s.weight for s in problem.already_assigned.get(m.id, []))
            for m in problem.members
        },
    )
    result = Result()

    # Hardest shifts first: fewest candidates per slot, then heaviest, then earliest.
    order = sorted(
        problem.shifts,
        key=lambda s: (candidate_count(s, problem) / s.slots, -s.weight, s.starts_at),
    )

    for shift in order:
        for _ in range(shift.slots):
            eligible = [
                m for m in problem.members if all(rule(m, shift, problem, state) for rule in rules)
            ]
            if not eligible:
                result.unfilled[shift.id] = result.unfilled.get(shift.id, 0) + 1
                continue
            chosen = min(eligible, key=lambda m: fairness_score(m, state))
            result.assignments.append((shift.id, chosen.id))
            state.shifts_of[chosen.id].append(shift)
            state.load[chosen.id] += shift.weight

    # Explain every gap. Rules only get stricter as shifts are handed out, so anyone
    # who couldn't take a slot when its turn came still can't at the end.
    for shift in problem.shifts:
        if shift.id in result.unfilled:
            result.blocked[shift.id] = [
                (m.id, reason)
                for m in problem.members
                if is_available(m, shift, problem, state)
                and (reason := blocking_reason(m, shift, problem, state, rules)) is not None
            ]

    return result
