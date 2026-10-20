"""Shift assignment in plain Python: no DB, so it can be tested on its own for now."""
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime


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
    max_shifts_per_member: int = 2


@dataclass
class Result:
    assignments: list[tuple[int, int]] = field(
        default_factory=list)  # (shift_id, member_id)
    unfilled: dict[int, int] = field(
        default_factory=dict)  # shift_id -> empty slots


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


def under_max(member: MemberIn, shift: ShiftIn, problem: Problem, state: State) -> bool:
    return len(state.shifts_of[member.id]) < problem.max_shifts_per_member


HARD_RULES: list[Rule] = [is_available,
                          not_already_on_shift, no_overlap, under_max]


# ---------- Greedy solver ----------
def fairness_score(member: MemberIn, state: State) -> tuple[int, int]:
    """Lower goes first: points already earned plus load taken on this round.
    The member id breaks ties, so the result is always the same for the same input."""
    return (member.points + state.load[member.id], member.id)


def candidate_count(shift: ShiftIn, problem: Problem) -> int:
    return sum(1 for m in problem.members if (m.id, shift.id) in problem.available)


def solve_greedy(problem: Problem, rules: list[Rule] = HARD_RULES) -> Result:
    state = State(
        shifts_of={m.id: [] for m in problem.members},
        load={m.id: 0 for m in problem.members},
    )
    result = Result()

    # Hardest shifts first: fewest candidates per slot, then heaviest, then earliest.
    order = sorted(
        problem.shifts,
        key=lambda s: (candidate_count(s, problem) /
                       s.slots, -s.weight, s.starts_at),
    )

    for shift in order:
        for _ in range(shift.slots):
            eligible = [
                m for m in problem.members
                if all(rule(m, shift, problem, state) for rule in rules)
            ]
            if not eligible:
                result.unfilled[shift.id] = result.unfilled.get(
                    shift.id, 0) + 1
                continue
            chosen = min(eligible, key=lambda m: fairness_score(m, state))
            result.assignments.append((shift.id, chosen.id))
            state.shifts_of[chosen.id].append(shift)
            state.load[chosen.id] += shift.weight

    return result
