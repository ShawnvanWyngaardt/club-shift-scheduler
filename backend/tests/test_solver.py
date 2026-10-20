from datetime import datetime

from solver import MemberIn, Problem, ShiftIn, solve_greedy


def make_shift(shift_id: int, day: int, start: int, end: int, weight: int = 1, slots: int = 1) -> ShiftIn:
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
        shifts=[make_shift(10, day=24, start=9, end=12),
                make_shift(11, day=24, start=11, end=14)],
        available={(1, 10), (1, 11)},
    )
    result = solve_greedy(problem)
    assert len(result.assignments) == 1
    assert sum(result.unfilled.values()) == 1


def test_respects_max_shifts_per_member():
    problem = Problem(
        members=[MemberIn(1, "Anna")],
        shifts=[make_shift(i, day=20 + i, start=9, end=12)
                for i in range(1, 4)],
        available={(1, 1), (1, 2), (1, 3)},
        max_shifts_per_member=1,
    )
    result = solve_greedy(problem)
    assert len(result.assignments) == 1
    assert sum(result.unfilled.values()) == 2


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
        shifts=[make_shift(10, day=24, start=9, end=12),
                make_shift(11, day=25, start=9, end=12)],
        available={(1, 10), (1, 11), (2, 10), (2, 11)},
    )
    assigned_members = {member_id for _,
                        member_id in solve_greedy(problem).assignments}
    assert assigned_members == {1, 2}
