from datetime import datetime

from solver import MemberIn, Problem, ShiftIn, solve_greedy


def make_shift(
    shift_id: int, day: int, start: int, end: int, weight: int = 1, slots: int = 1
) -> ShiftIn:
    return ShiftIn(
        id=shift_id,
        starts_at=datetime(2026, 10, day, start),
        ends_at=datetime(2026, 10, day, end),
        weight=weight,
        slots=slots,
    )


def test_fills_shift_with_available_member():
    problem = Problem(
        members=[MemberIn(1, "Anna")],
        shifts=[make_shift(10, day=24, start=9, end=12)],
        available={(1, 10)},
    )
    result = solve_greedy(problem)
    assert result.assignments == [(10, 1)]
    assert result.unfilled == {}


def test_never_assigns_unavailable_member():
    problem = Problem(
        members=[MemberIn(1, "Anna"), MemberIn(2, "Bram")],
        shifts=[make_shift(10, day=24, start=9, end=12)],
        available={(2, 10)},
    )
    assert solve_greedy(problem).assignments == [(10, 2)]


def test_no_overlapping_shifts_for_one_member():
    problem = Problem(
        members=[MemberIn(1, "Anna")],
        shifts=[make_shift(10, day=24, start=9, end=12), make_shift(11, day=24, start=11, end=14)],
        available={(1, 10), (1, 11)},
    )
    result = solve_greedy(problem)
    assert len(result.assignments) == 1
    assert sum(result.unfilled.values()) == 1


def test_one_willing_member_takes_every_shift_they_offered():
    problem = Problem(
        members=[MemberIn(1, "Anna")],
        shifts=[make_shift(i, day=20 + i, start=9, end=12) for i in range(1, 4)],
        available={(1, 1), (1, 2), (1, 3)},
    )
    result = solve_greedy(problem)
    assert len(result.assignments) == 3
    assert result.unfilled == {}


def test_reports_impossible_shift_instead_of_failing():
    problem = Problem(
        members=[MemberIn(1, "Anna")],
        shifts=[make_shift(10, day=24, start=7, end=10, slots=2)],
        available=set(),
    )
    result = solve_greedy(problem)
    assert result.assignments == []
    assert result.unfilled == {10: 2}


def test_lowest_points_gets_the_unpopular_shift():
    problem = Problem(
        members=[MemberIn(1, "Anna", points=5), MemberIn(2, "Bram", points=0)],
        shifts=[make_shift(10, day=24, start=7, end=10, weight=3)],
        available={(1, 10), (2, 10)},
    )
    assert solve_greedy(problem).assignments == [(10, 2)]


def test_spreads_load_between_equal_members():
    problem = Problem(
        members=[MemberIn(1, "Anna"), MemberIn(2, "Bram")],
        shifts=[make_shift(10, day=24, start=9, end=12), make_shift(11, day=25, start=9, end=12)],
        available={(1, 10), (1, 11), (2, 10), (2, 11)},
    )
    assigned_members = {member_id for _, member_id in solve_greedy(problem).assignments}
    assert assigned_members == {1, 2}


def test_shifts_already_held_count_for_overlaps():
    held = make_shift(10, day=24, start=9, end=12)
    problem = Problem(
        members=[MemberIn(1, "Anna")],
        shifts=[make_shift(11, day=24, start=11, end=13)],
        available={(1, 11)},
        already_assigned={1: [held]},
    )
    result = solve_greedy(problem)
    assert result.assignments == []
    assert result.unfilled == {11: 1}


def test_member_with_earlier_shifts_still_fills_a_gap_nobody_else_can():
    held = [make_shift(10, day=14, start=8, end=9), make_shift(11, day=14, start=9, end=12)]
    problem = Problem(
        members=[MemberIn(1, "Ava"), MemberIn(2, "Dirk")],
        shifts=[make_shift(12, day=21, start=9, end=12)],
        available={(1, 12)},
        already_assigned={1: held},
    )
    assert solve_greedy(problem).assignments == [(12, 1)]


def test_explains_why_a_slot_stays_empty():
    held = make_shift(10, day=24, start=9, end=12)
    problem = Problem(
        members=[MemberIn(1, "Anna"), MemberIn(2, "Bram"), MemberIn(3, "Cas")],
        shifts=[
            make_shift(11, day=24, start=11, end=13, slots=3),
            make_shift(12, day=25, start=9, end=12),
        ],
        available={(1, 11), (2, 11)},
        already_assigned={1: [held]},
    )
    result = solve_greedy(problem)
    assert result.assignments == [(11, 2)]
    assert result.unfilled == {11: 2, 12: 1}
    assert sorted(result.blocked[11]) == [(1, "busy_at_that_time"), (2, "already_on_shift")]
    assert result.blocked[12] == []
