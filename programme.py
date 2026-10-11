#!/usr/bin/env python3
"""
programme.py - the order the work has to happen in, derived.

    python3 programme.py           the stages, to the terminal

The register says what is produced and who is competent to produce it.  It
does not say when, and until now nothing in the project did: eighty-three
deliverables with no statement of which can start today and which cannot
start until somebody else has done something.  That gap is what this
module closes.

**The sequence is derived, not typed.**  Every row in `deliverables.py`
already carries `depends`, and those dependencies are the programme: a row
can start when everything it waits on is finished, and not before.  So the
stages here are computed from the graph the register already holds -
`stage()` is the longest path to a row, which is the earliest stage it can
possibly sit in - rather than written down a second time in an order
somebody judged by eye.  A dependency added to a row moves it, and
everything behind it, on the next build.

**There are no durations and no dates, and that is the point.**  How long
a measured survey takes, how long a municipality holds a permit, how long
an engineer needs for six framing layouts, what a contractor will commit
to: every one of those is class X - external, unknowable here, and the
kind of figure that gets quoted back as a commitment the moment it appears
on a page.  A bar chart with invented bar lengths is the programme
equivalent of a foundation detail with invented rebar, and this project
does not issue those.  So the duration column is open, exactly as QS-004's
rate column is open, and it says who fills it.

What that leaves is still worth having, because it is true:

    the sequence          which deliverable waits on which, in stages
    the critical chain    the longest path through the register, so the
                          longest thing in the project is named rather
                          than discovered late
    the gates             what each class X row holds up, counted

A reader who wants dates takes this and adds durations from the people who
own them.  A reader who wants to know what is holding up the structural
package can read it off the gates today.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import deliverables as DL


class Circular(ValueError):
    """A dependency that leads back to itself.

    `checks.py` already refuses a circle in the register, so this should
    be unreachable - but the stage walk recurses, and an unreachable
    circle would otherwise arrive as a RecursionError a thousand frames
    deep with nothing in it naming the deliverables involved.  Raised
    with the cycle in the message instead.
    """


def _graph(rows=None):
    rows = rows if rows is not None else DL.register()
    return rows, {r.code: r for r in rows}


def stage(code, index=None, _path=()):
    """The earliest stage a deliverable can sit in, counting from 0.

    The longest path to it: a row sits one stage behind the last of the
    things it waits on, so a row in stage 3 has at least three
    deliverables that must finish in order before it starts.  Not the
    shortest path - a row is not ready when one of its dependencies is
    done, it is ready when all of them are.

    A dependency outside the register scores nothing rather than raising.
    checks.py fails the build on one, which is the right place for it;
    here it would only stop the programme printing on the very run that
    is trying to tell you what is wrong.
    """
    _rows, index = _graph() if index is None else (None, index)
    if code in _path:
        raise Circular(" -> ".join(_path + (code,)))
    row = index.get(code)
    if row is None or not row.depends:
        return 0
    return 1 + max(stage(d, index, _path + (code,)) for d in row.depends)


def stages(rows=None):
    """[(n, [rows])] - every deliverable in the earliest stage it can sit in.

    Stage 0 is large, and that is the useful first fact about this
    project rather than a defect in the measure: most of the architecture
    waits on nothing and could be drawn the day the brief is agreed.  The
    programme's substance is the tail.
    """
    rows, index = _graph(rows)
    out = {}
    for r in rows:
        out.setdefault(stage(r.code, index), []).append(r)
    return [(n, out[n]) for n in sorted(out)]


def chain(code, index=None):
    """The longest dependency chain ending at a deliverable, earliest first.

    This is the path that sets the row's stage: the one sequence of
    deliverables that has to happen one after another before it can
    start.
    """
    _rows, index = _graph() if index is None else (None, index)
    row = index.get(code)
    if row is None:
        return []
    if not row.depends:
        return [code]
    longest = max((chain(d, index) for d in row.depends), key=len)
    return longest + [code]


def critical_chain(rows=None):
    """The longest path through the whole register.

    The project's own lower bound: nothing can compress this sequence,
    because every step in it waits on the one before.  Named here so that
    the longest thing in the project is known at the start rather than
    found out at the end.
    """
    rows, index = _graph(rows)
    return max((chain(r.code, index) for r in rows), key=len)


def dependents(code, rows=None):
    """Every deliverable that cannot finish until this one has, transitively.

    What a row holds up.  Used for the gates, where the number is the
    whole argument: SUR-001 is one line in the register and a large part
    of the project behind it.
    """
    rows, _index = _graph(rows)
    held, growing = set(), True
    while growing:
        growing = False
        for r in rows:
            if r.code in held:
                continue
            if code in r.depends or held & set(r.depends):
                held.add(r.code)
                growing = True
    return held


def gates(rows=None):
    """[(row, [codes it holds up])] for every class X deliverable, worst first.

    A gate is a row the project cannot produce at all - a survey, a soil
    report, a contractor's commitment.  Everything behind it is work that
    is ready in every other respect and still cannot start, which is the
    one thing a programme is for.
    """
    rows, _index = _graph(rows)
    out = [(r, sorted(dependents(r.code, rows))) for r in rows
           if r.klass == "X"]
    return sorted(out, key=lambda pair: (-len(pair[1]), pair[0].code))


def can_start_now(rows=None):
    """The deliverables waiting on nothing - the work available today."""
    rows, _index = _graph(rows)
    return [r for r in rows if not r.depends]


def summary(rows=None):
    """(stages, longest chain, rows behind a gate) - for the status line."""
    rows, _index = _graph(rows)
    behind = set()
    for r, held in gates(rows):
        behind |= set(held)
    return len(stages(rows)), critical_chain(rows), sorted(behind)


def main():
    rows = DL.register()
    for n, group in stages(rows):
        print(f"\nSTAGE {n} ({len(group)})")
        for r in group:
            waits = ", ".join(r.depends) or "-"
            print(f"  {r.code:9s} {r.klass}  {r.title[:46]:46s} {waits}")

    print("\ncritical chain:", " -> ".join(critical_chain(rows)))
    print("\ngates")
    for r, held in gates(rows):
        print(f"  {r.code:9s} holds up {len(held):2d}  {r.title}")
    n, longest, behind = summary(rows)
    print(f"\n{len(rows)} deliverables in {n} stages; longest chain "
          f"{len(longest)}; {len(behind)} rows behind a gate")
    print("no durations and no dates: both are class X")


if __name__ == "__main__":
    main()
