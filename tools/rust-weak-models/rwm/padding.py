"""Deterministic neutral padding for prompt-budget equalisation.

The GUIDED listing is longer than the PLAIN one because it has more types. To keep
the prompt budget equal across variants (a fairness control requested for this
experiment), the shorter variant's appendix is extended with example exports until
both prompts have the same token count. The examples are valid `mbx 1` texts from a
seeded generator that mirrors the library writer's format; they carry no API
information (a solution can never write export text itself), so they add length
without adding guidance. `--budget natural` in the runner turns padding off.
"""
from __future__ import annotations

import random

SIDES = ["WEST", "EAST", "RESISTANCE"]
SOLDIERS = ["RIFLEMAN", "MACHINE_GUNNER", "AT_SOLDIER", "MEDIC", "OFFICER"]
VEHICLES = ["TRUCK", "JEEP", "APC"]
RANKS = ["PRIVATE", "CORPORAL", "SERGEANT", "LIEUTENANT", "CAPTAIN"]
CALLSIGNS = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Kilo", "Lima", "Sierra", "Tango"]
RADIO = ["ALPHA", "BRAVO", "CHARLIE", "DELTA"]


def _n(v: float) -> str:
    return f"{v:.1f}"


def example_export(seed: int) -> str:
    """One valid example mission in the library's export format."""
    rng = random.Random(seed)
    lines = ["mbx 1"]
    unit_no = 0
    groups = []
    for gi in range(rng.randint(1, 3)):
        side = rng.choice(SIDES)
        callsign = CALLSIGNS[(seed + gi * 3) % len(CALLSIGNS)] + ("" if gi == 0 else f"-{gi}")
        cx, cz = rng.uniform(1000, 11000), rng.uniform(1000, 11000)
        units = []
        for _ in range(rng.randint(1, 4)):
            cls = rng.choice(SOLDIERS)
            units.append((unit_no, cls, f"{callsign[0].lower()}{unit_no}", cx + rng.uniform(-40, 40), cz + rng.uniform(-40, 40), rng.choice(RANKS)))
            unit_no += 1
        vehicle = None
        if rng.random() < 0.4:
            vcls = rng.choice(VEHICLES)
            vehicle = unit_no
            units.append((unit_no, vcls, f"{vcls.lower()}{unit_no}", cx + 15, cz - 10, "PRIVATE"))
            unit_no += 1
        ranks = [RANKS.index(u[5]) for u in units]
        leader = units[ranks.index(max(ranks))][0]
        lines.append(f'group g{gi} "{callsign}" {side} leader u{leader}')
        for u in units:
            lines.append(f'unit u{u[0]} g{gi} {u[1]} "{u[2]}" {_n(u[3])} {_n(u[4])} {u[5]}')
        wps = []
        if vehicle is not None:
            wps.append(f"GET_IN u{vehicle}")
            wps.append(f"MOVE {_n(cx + 600)} {_n(cz + 300)}")
            wps.append(f"GET_OUT {_n(cx + 620)} {_n(cz + 310)}")
        kind = rng.choice(["patrol", "hold", "open"])
        pts = [(cx + rng.uniform(-900, 900), cz + rng.uniform(-900, 900)) for _ in range(rng.randint(2, 3))]
        for x, z in pts:
            wps.append(f"{rng.choice(['MOVE', 'MOVE', 'SEEK_AND_DESTROY'])} {_n(x)} {_n(z)}")
        if kind == "patrol":
            wps.append("CYCLE")
        elif kind == "hold":
            wps.append(f"HOLD {_n(pts[-1][0])} {_n(pts[-1][1])}")
        for i, w in enumerate(wps):
            lines.append(f"wp g{gi} {i} {w}")
        groups.append((gi, len(wps)))
    if len(groups) > 1 and groups[0][1] > 1 and groups[1][1] > 1:
        lines.append(f"sync g0 1 g1 {rng.randint(0, groups[1][1] - 2)}")
    for ti in range(rng.randint(1, 2)):
        x, z = rng.uniform(1500, 11000), rng.uniform(1500, 11000)
        a = rng.choice([50, 100, 150, 250])
        act = rng.choice([f"RADIO {rng.choice(RADIO)}", f"PRESENT {rng.choice(SIDES)}", f"NOT_PRESENT {rng.choice(SIDES)}", "NONE"])
        effect = rng.choice(["NONE", "END 1", "END 2", "LOSE"])
        repeat = "ONCE" if effect != "NONE" or rng.random() < 0.5 else "REPEATEDLY"
        if rng.random() < 0.5:
            lo = rng.choice([10, 30, 60])
            timer = f"{rng.choice(['COUNTDOWN', 'TIMEOUT'])} {_n(lo)} {_n(lo * 2)} {_n(lo * 3)}"
        else:
            timer = "NONE"
        lines.append(f"trigger t{ti} area {_n(x)} {_n(z)} {_n(a)} {_n(a)} {_n(0)} act {act} repeat {repeat} timer {timer} effect {effect}")
        if groups and groups[0][1] > 0 and rng.random() < 0.5:
            lines.append(f"tsync t{ti} g0 0")
    lines.append("end")
    return "\n".join(lines)


def padding_text(target_tokens: int, count_tokens, seed: int = 20260928) -> str:
    """Example exports appended until `count_tokens(text)` reaches `target_tokens`.

    Grows one example at a time, then trims whole lines from the end so the result
    never overshoots the target (the caller accepts a small undershoot)."""
    if target_tokens <= 0:
        return ""
    parts: list[str] = []
    k = 0
    text = ""
    while count_tokens(text) < target_tokens and k < 400:
        parts.append(f"Example export {k + 1}:\n```text\n{example_export(seed + k)}\n```")
        text = "\n\n".join(parts)
        k += 1
    lines = text.splitlines()
    while lines and count_tokens("\n".join(lines)) > target_tokens:
        lines.pop()
    # Close an open code fence so the prompt stays well-formed.
    if sum(1 for ln in lines if ln.startswith("```")) % 2 == 1:
        lines.append("```")
    return "\n".join(lines)
