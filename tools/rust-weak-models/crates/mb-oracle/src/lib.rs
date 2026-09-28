//! Independent parser and rule checker for `mbx 1` text.
//!
//! Used only by the task tests (visible and hidden). It shares no code with the
//! library (`mb-core`) so that the tests judge the exported text itself. Query
//! helpers panic with a readable message when something is missing, because they
//! run inside `#[test]` functions where a panic is the failure signal.

/// Parsed mission.
#[derive(Debug, Clone, PartialEq, Default)]
pub struct Doc {
    pub note: Option<String>,
    pub groups: Vec<Group>,
    pub syncs: Vec<(WpKey, WpKey)>,
    pub triggers: Vec<Trigger>,
}

/// Waypoint address by group key (`g0`) and 0-based index.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WpKey {
    pub group: String,
    pub index: usize,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Group {
    pub key: String,
    pub callsign: String,
    pub side: String,
    pub leader: Option<String>,
    pub units: Vec<Unit>,
    pub wps: Vec<Wp>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Unit {
    pub key: String,
    pub class: String,
    pub label: String,
    pub x: f64,
    pub z: f64,
    pub rank: String,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Wp {
    pub kind: String,
    pub pos: Option<(f64, f64)>,
    pub vehicle: Option<String>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Trigger {
    pub key: String,
    /// centre x, centre z, a, b, angle
    pub area: [f64; 5],
    /// e.g. `["RADIO", "ALPHA"]`, `["PRESENT", "WEST"]`, `["DETECTED_BY", det, detected]`
    pub act: Vec<String>,
    pub repeat: String,
    /// kind, min, mid, max (seconds)
    pub timer: Option<(String, f64, f64, f64)>,
    /// `"NONE"`, `"LOSE"` or `"END n"`
    pub effect: String,
    pub syncs: Vec<WpKey>,
}

const MAP: f64 = 12_800.0;
const VEHICLES: [&str; 3] = ["TRUCK", "JEEP", "APC"];

fn on_map(x: f64, z: f64) -> bool {
    (0.0..=MAP).contains(&x) && (0.0..=MAP).contains(&z)
}

/// True if two exported numbers are equal up to the one-decimal formatting.
pub fn near(a: f64, b: f64) -> bool {
    (a - b).abs() <= 0.06
}

// ── Tokenizer ────────────────────────────────────────────────────────────────

fn tokens(line: &str) -> Result<Vec<String>, String> {
    let mut out = Vec::new();
    let mut chars = line.chars().peekable();
    while let Some(&c) = chars.peek() {
        if c == ' ' {
            chars.next();
            continue;
        }
        if c == '"' {
            chars.next();
            let mut s = String::from("\u{1}"); // marks a quoted token
            loop {
                match chars.next() {
                    None => return Err(format!("unterminated string in: {line}")),
                    Some('"') => break,
                    Some('\\') => match chars.next() {
                        Some('n') => s.push('\n'),
                        Some('"') => s.push('"'),
                        Some('\\') => s.push('\\'),
                        other => return Err(format!("bad escape {other:?} in: {line}")),
                    },
                    Some(ch) => s.push(ch),
                }
            }
            out.push(s);
        } else {
            let mut s = String::new();
            while let Some(&ch) = chars.peek() {
                if ch == ' ' {
                    break;
                }
                s.push(ch);
                chars.next();
            }
            out.push(s);
        }
    }
    Ok(out)
}

fn quoted(t: Option<&String>) -> Result<String, String> {
    match t {
        Some(s) if s.starts_with('\u{1}') => Ok(s.trim_start_matches('\u{1}').to_string()),
        other => Err(format!("expected quoted string, got {other:?}")),
    }
}

fn word(t: Option<&String>) -> Result<String, String> {
    match t {
        Some(s) if !s.starts_with('\u{1}') => Ok(s.clone()),
        other => Err(format!("expected word, got {other:?}")),
    }
}

fn number(t: Option<&String>) -> Result<f64, String> {
    let w = word(t)?;
    w.parse::<f64>().map_err(|_| format!("expected number, got {w:?}"))
}

fn index(t: Option<&String>) -> Result<usize, String> {
    let w = word(t)?;
    w.parse::<usize>().map_err(|_| format!("expected index, got {w:?}"))
}

// ── Parser ───────────────────────────────────────────────────────────────────

/// Parses `mbx 1` text. Structural errors (unknown line kinds, bad tokens, out of
/// order indices, missing `end`) are reported as `Err(message)`.
pub fn parse(text: &str) -> Result<Doc, String> {
    let mut doc = Doc::default();
    let mut lines = text.lines();
    if lines.next() != Some("mbx 1") {
        return Err("first line must be `mbx 1`".into());
    }
    let mut ended = false;
    for line in lines {
        if ended {
            return Err(format!("text after `end`: {line}"));
        }
        let t = tokens(line)?;
        let kind = t.first().map(String::as_str).unwrap_or("");
        match kind {
            "end" => ended = true,
            "note" => doc.note = Some(quoted(t.get(1))?),
            "group" => doc.groups.push(Group {
                key: word(t.get(1))?,
                callsign: quoted(t.get(2))?,
                side: word(t.get(3))?,
                leader: {
                    if word(t.get(4))? != "leader" {
                        return Err(format!("missing leader in: {line}"));
                    }
                    let l = word(t.get(5))?;
                    if l == "-" { None } else { Some(l) }
                },
                units: Vec::new(),
                wps: Vec::new(),
            }),
            "unit" => {
                let key = word(t.get(1))?;
                let gkey = word(t.get(2))?;
                let unit = Unit {
                    key,
                    class: word(t.get(3))?,
                    label: quoted(t.get(4))?,
                    x: number(t.get(5))?,
                    z: number(t.get(6))?,
                    rank: word(t.get(7))?,
                };
                let g = doc.groups.iter_mut().find(|g| g.key == gkey).ok_or(format!("unit of unknown group: {line}"))?;
                g.units.push(unit);
            }
            "wp" => {
                let gkey = word(t.get(1))?;
                let i = index(t.get(2))?;
                let wkind = word(t.get(3))?;
                let wp = match wkind.as_str() {
                    "MOVE" | "SEEK_AND_DESTROY" | "HOLD" | "GET_OUT" => {
                        Wp { kind: wkind, pos: Some((number(t.get(4))?, number(t.get(5))?)), vehicle: None }
                    }
                    "GET_IN" => Wp { kind: wkind, pos: None, vehicle: Some(word(t.get(4))?) },
                    "CYCLE" => Wp { kind: wkind, pos: None, vehicle: None },
                    other => return Err(format!("unknown waypoint kind {other}")),
                };
                let g = doc.groups.iter_mut().find(|g| g.key == gkey).ok_or(format!("wp of unknown group: {line}"))?;
                if i != g.wps.len() {
                    return Err(format!("waypoint index out of order: {line}"));
                }
                g.wps.push(wp);
            }
            "sync" => doc.syncs.push((
                WpKey { group: word(t.get(1))?, index: index(t.get(2))? },
                WpKey { group: word(t.get(3))?, index: index(t.get(4))? },
            )),
            "trigger" => doc.triggers.push(parse_trigger(&t, line)?),
            "tsync" => {
                let tkey = word(t.get(1))?;
                let at = WpKey { group: word(t.get(2))?, index: index(t.get(3))? };
                let tr = doc.triggers.iter_mut().find(|x| x.key == tkey).ok_or(format!("tsync of unknown trigger: {line}"))?;
                tr.syncs.push(at);
            }
            other => return Err(format!("unknown line kind {other:?}")),
        }
    }
    if !ended {
        return Err("missing `end`".into());
    }
    Ok(doc)
}

fn parse_trigger(t: &[String], line: &str) -> Result<Trigger, String> {
    let key = word(t.get(1))?;
    let expect = |i: usize, w: &str| -> Result<(), String> {
        if word(t.get(i))? == w { Ok(()) } else { Err(format!("expected {w} at {i} in: {line}")) }
    };
    expect(2, "area")?;
    let area = [number(t.get(3))?, number(t.get(4))?, number(t.get(5))?, number(t.get(6))?, number(t.get(7))?];
    expect(8, "act")?;
    let mut i = 9;
    let mut act = Vec::new();
    while let Some(w) = t.get(i) {
        if w == "repeat" {
            break;
        }
        act.push(w.clone());
        i += 1;
    }
    expect(i, "repeat")?;
    let repeat = word(t.get(i + 1))?;
    expect(i + 2, "timer")?;
    let tkind = word(t.get(i + 3))?;
    let (timer, next) = if tkind == "NONE" {
        (None, i + 4)
    } else {
        (Some((tkind, number(t.get(i + 4))?, number(t.get(i + 5))?, number(t.get(i + 6))?)), i + 7)
    };
    expect(next, "effect")?;
    let effect = t.get(next + 1..).map(|r| r.join(" ")).unwrap_or_default();
    Ok(Trigger { key, area, act, repeat, timer, effect, syncs: Vec::new() })
}

// ── Rule checker ─────────────────────────────────────────────────────────────

/// Every rule violation (R1-R10 and leader membership) as readable strings.
pub fn violations(doc: &Doc) -> Vec<String> {
    let mut v = Vec::new();
    for (gi, g) in doc.groups.iter().enumerate() {
        let cs = &g.callsign;
        if g.units.is_empty() {
            v.push(format!("R9 group {cs:?} has no units"));
        }
        if doc.groups.iter().take(gi).any(|o| o.callsign == g.callsign) {
            v.push(format!("R9 duplicate callsign {cs:?}"));
        }
        match &g.leader {
            Some(l) if !g.units.iter().any(|u| &u.key == l) => v.push(format!("leader {l} not in group {cs:?}")),
            None if !g.units.is_empty() => v.push(format!("group {cs:?} has no leader")),
            _ => {}
        }
        for u in &g.units {
            if !on_map(u.x, u.z) {
                v.push(format!("R10 unit {:?} at ({}, {}) off the map", u.label, u.x, u.z));
            }
        }
        let mut moves = 0;
        let mut mounted = false;
        let mut held = false;
        for (i, w) in g.wps.iter().enumerate() {
            if held {
                v.push(format!("R2 {cs:?} waypoint {i} after HOLD"));
            }
            if let Some((x, z)) = w.pos {
                if !on_map(x, z) {
                    v.push(format!("R10 {cs:?} waypoint {i} off the map"));
                }
            }
            match w.kind.as_str() {
                "MOVE" | "SEEK_AND_DESTROY" => moves += 1,
                "HOLD" => held = true,
                "GET_IN" => {
                    mounted = true;
                    let key = w.vehicle.clone().unwrap_or_default();
                    match doc.unit(&key) {
                        None => v.push(format!("R4 {cs:?} GET_IN unknown unit {key}")),
                        Some((vg, vu)) => {
                            if !VEHICLES.contains(&vu.class.as_str()) {
                                v.push(format!("R4 {cs:?} GET_IN {key} is not a vehicle"));
                            }
                            if vg.side != g.side {
                                v.push(format!("R4 {cs:?} GET_IN {key} of side {}", vg.side));
                            }
                        }
                    }
                }
                "GET_OUT" => {
                    if !mounted {
                        v.push(format!("R3 {cs:?} GET_OUT at {i} without GET_IN"));
                    }
                    mounted = false;
                }
                "CYCLE" => {
                    if i + 1 != g.wps.len() {
                        v.push(format!("R1 {cs:?} CYCLE at {i} is not last"));
                    }
                    if moves < 2 {
                        v.push(format!("R1 {cs:?} CYCLE after {moves} moves"));
                    }
                }
                _ => {}
            }
        }
    }
    let exists = |k: &WpKey| doc.groups.iter().any(|g| g.key == k.group && k.index < g.wps.len());
    for (a, b) in &doc.syncs {
        for k in [a, b] {
            if !exists(k) {
                v.push(format!("R5 sync to missing waypoint {}:{}", k.group, k.index));
            }
        }
    }
    for tr in &doc.triggers {
        if !on_map(tr.area[0], tr.area[1]) {
            v.push(format!("R10 trigger {} centre off the map", tr.key));
        }
        if let Some((_, lo, md, hi)) = tr.timer {
            if !(lo <= md && md <= hi && lo >= 0.0) {
                v.push(format!("R6 trigger {} timer {lo}/{md}/{hi}", tr.key));
            }
        }
        if tr.act.first().map(String::as_str) == Some("DETECTED_BY") && tr.act.get(1) == tr.act.get(2) {
            v.push(format!("R7 trigger {} side detects itself", tr.key));
        }
        if tr.effect != "NONE" && tr.repeat != "ONCE" {
            v.push(format!("R8 trigger {} ends the mission but repeats", tr.key));
        }
        for k in &tr.syncs {
            if !exists(k) {
                v.push(format!("R5 trigger {} synced to missing waypoint {}:{}", tr.key, k.group, k.index));
            }
        }
    }
    v
}

/// Parses and checks; panics (failing the test) on a parse error or any violation.
pub fn accept(text: &str) -> Doc {
    let doc = match parse(text) {
        Ok(d) => d,
        Err(e) => panic!("export does not parse: {e}"),
    };
    let v = violations(&doc);
    if !v.is_empty() {
        panic!("export breaks the domain rules: {v:?}");
    }
    doc
}

// ── Queries for tests ────────────────────────────────────────────────────────

impl Doc {
    /// The group with this callsign, if any.
    pub fn find_group(&self, callsign: &str) -> Option<&Group> {
        self.groups.iter().find(|g| g.callsign == callsign)
    }

    /// The group with this callsign; panics if missing.
    pub fn group(&self, callsign: &str) -> &Group {
        self.find_group(callsign).unwrap_or_else(|| panic!("no group {callsign:?} in export"))
    }

    /// Callsigns in export order.
    pub fn callsigns(&self) -> Vec<&str> {
        self.groups.iter().map(|g| g.callsign.as_str()).collect()
    }

    /// Unit by key (`u3`) with its group.
    pub fn unit(&self, key: &str) -> Option<(&Group, &Unit)> {
        self.groups.iter().find_map(|g| g.units.iter().find(|u| u.key == key).map(|u| (g, u)))
    }

    /// First unit with this label, with its group.
    pub fn unit_by_label(&self, label: &str) -> Option<(&Group, &Unit)> {
        self.groups.iter().find_map(|g| g.units.iter().find(|u| u.label == label).map(|u| (g, u)))
    }

    /// Label of the group's leader; panics if the group or leader is missing.
    pub fn leader_label(&self, callsign: &str) -> String {
        let g = self.group(callsign);
        let key = g.leader.clone().unwrap_or_else(|| panic!("group {callsign:?} has no leader"));
        self.unit(&key).map(|(_, u)| u.label.clone()).unwrap_or_else(|| panic!("leader {key} missing"))
    }

    /// Waypoint kinds of a group, in order.
    pub fn kinds(&self, callsign: &str) -> Vec<String> {
        self.group(callsign).wps.iter().map(|w| w.kind.clone()).collect()
    }

    /// Waypoint `index` of a group; panics if missing.
    pub fn wp(&self, callsign: &str, index: usize) -> &Wp {
        self.group(callsign)
            .wps
            .get(index)
            .unwrap_or_else(|| panic!("group {callsign:?} has no waypoint {index}"))
    }

    /// Label of the vehicle a GET_IN waypoint boards.
    pub fn boarded_label(&self, callsign: &str, index: usize) -> String {
        let w = self.wp(callsign, index);
        let key = w.vehicle.clone().unwrap_or_else(|| panic!("{callsign:?} waypoint {index} is not GET_IN"));
        self.unit(&key).map(|(_, u)| u.label.clone()).unwrap_or_else(|| panic!("vehicle {key} missing"))
    }

    fn key_of(&self, callsign: &str) -> String {
        self.group(callsign).key.clone()
    }

    /// True if the two waypoints are synchronised (either order).
    pub fn synced(&self, a: (&str, usize), b: (&str, usize)) -> bool {
        let ka = WpKey { group: self.key_of(a.0), index: a.1 };
        let kb = WpKey { group: self.key_of(b.0), index: b.1 };
        self.syncs.iter().any(|(x, y)| (x == &ka && y == &kb) || (x == &kb && y == &ka))
    }

    /// Trigger syncs of trigger `t` as `(callsign, index)` pairs.
    pub fn trigger_syncs(&self, t: usize) -> Vec<(String, usize)> {
        let tr = self.triggers.get(t).unwrap_or_else(|| panic!("no trigger {t}"));
        tr.syncs
            .iter()
            .map(|k| {
                let cs = self.groups.iter().find(|g| g.key == k.group).map(|g| g.callsign.clone()).unwrap_or_default();
                (cs, k.index)
            })
            .collect()
    }

    /// Triggers whose activation starts with these words, e.g. `&["RADIO", "ALPHA"]`.
    pub fn triggers_with_act(&self, act: &[&str]) -> Vec<&Trigger> {
        self.triggers.iter().filter(|t| t.act.iter().map(String::as_str).eq(act.iter().copied())).collect()
    }

    /// Total number of units.
    pub fn unit_count(&self) -> usize {
        self.groups.iter().map(|g| g.units.len()).sum()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const SAMPLE: &str = "mbx 1\nnote \"a \\\"b\\\"\"\ngroup g0 \"Alpha\" WEST leader u1\nunit u0 g0 RIFLEMAN \"a1\" 10.0 20.0 PRIVATE\nunit u1 g0 TRUCK \"t 1\" 30.0 40.0 SERGEANT\nwp g0 0 MOVE 1.0 2.0\nwp g0 1 GET_IN u1\nwp g0 2 GET_OUT 3.0 4.0\nwp g0 3 MOVE 5.0 6.0\nwp g0 4 CYCLE\ntrigger t0 area 100.0 100.0 50.0 50.0 0.0 act RADIO ALPHA repeat ONCE timer COUNTDOWN 1.0 2.0 3.0 effect END 1\ntsync t0 g0 1\nend\n";

    /// A well-formed sample parses and satisfies every rule.
    #[test]
    fn sample_parses_and_is_valid() {
        let d = accept(SAMPLE);
        assert_eq!(d.note.as_deref(), Some("a \"b\""));
        assert_eq!(d.kinds("Alpha"), vec!["MOVE", "GET_IN", "GET_OUT", "MOVE", "CYCLE"]);
        assert_eq!(d.boarded_label("Alpha", 1), "t 1");
        assert_eq!(d.trigger_syncs(0), vec![("Alpha".to_string(), 1)]);
        assert_eq!(d.triggers_with_act(&["RADIO", "ALPHA"]).len(), 1);
        assert_eq!(d.leader_label("Alpha"), "t 1");
    }

    /// Each rule the oracle knows is detected on a crafted violation.
    #[test]
    fn violations_are_detected() {
        let bad = SAMPLE
            .replace("wp g0 4 CYCLE", "wp g0 4 CYCLE\nwp g0 5 MOVE 1.0 1.0")
            .replace("repeat ONCE", "repeat REPEATEDLY")
            .replace("COUNTDOWN 1.0 2.0 3.0", "COUNTDOWN 3.0 2.0 1.0");
        let v = violations(&parse(&bad).unwrap());
        assert!(v.iter().any(|s| s.starts_with("R1")), "{v:?}");
        assert!(v.iter().any(|s| s.starts_with("R6")), "{v:?}");
        assert!(v.iter().any(|s| s.starts_with("R8")), "{v:?}");
    }
}
