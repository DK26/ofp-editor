// SPDX-License-Identifier: GPL-3.0-or-later
//! `xtask hygiene`: no third-party marks or island names in the names of what this repository makes.
//!
//! **What.** `AGENTS.md` ("Naming and Trademarks") and crate-map §15 forbid the game's marks and island names in
//! crate, binary, module, file-format, sidecar and generated-header names; the game is named only in descriptive
//! text. This module checks *names*, never prose: crate and target names from `cargo metadata`, file and folder
//! names under each workspace crate and `fuzz/fuzz_targets/` (which covers module files, fixtures, and format or
//! sidecar files named after their format), and inline `mod` declarations. String constants that name a format or
//! sidecar inside code are not scanned yet: they get a typed registry with its own check when the first one exists.
//!
//! **How.** [`MARKS`] is the one list. A name is split into lowercase tokens twice (on separators and letter/digit
//! boundaries, and again on camel-case boundaries, so `OFPEditor`, `ofp_editor` and `ArmA` all yield a match),
//! and each mark matches by [`MatchRule`]: short marks as whole tokens, `ofp` also as a token prefix, long marks
//! anywhere in the name with separators removed. A name with characters outside printable ASCII is reported on
//! its own, because a zero-width or look-alike character would hide a mark from this check.
//!
//! **Not covered.** Names of private projects (testing-strategy §14's public-hygiene grep) cannot be listed in a
//! public repository; that check needs a list kept outside it and is not part of this command.

use std::collections::BTreeSet;
use std::fmt;

use crate::display_name;
use crate::metadata::Metadata;

/// How a mark is matched against a name.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum MatchRule {
    /// Equal to a whole token (`arma` matches `arma_tools` and `ArmaTools`, not `armadillo`).
    Token,
    /// The start of a token (`ofp` also matches `ofpe` and `ofpeditor`, the research working names).
    TokenPrefix,
    /// Anywhere in the lowercase name with every separator removed (`coldwarassault` matches
    /// `cold_war_assault`); used only for marks long and distinctive enough not to occur inside ordinary words.
    Squashed,
}

/// What kind of name a mark is.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum MarkKind {
    /// A trademark or product name of the game's publishers.
    Trademark,
    /// An island of the game, by its display name or its engine world name.
    Island,
}

/// One entry of [`MARKS`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Mark {
    text: &'static str,
    rule: MatchRule,
    kind: MarkKind,
}

impl Mark {
    const fn new(text: &'static str, rule: MatchRule, kind: MarkKind) -> Self {
        Self { text, rule, kind }
    }

    /// The mark, lowercase, without separators.
    pub const fn text(&self) -> &'static str {
        self.text
    }

    /// How it is matched.
    pub const fn rule(&self) -> MatchRule {
        self.rule
    }

    /// Whether it is a trademark or an island name.
    pub const fn kind(&self) -> MarkKind {
        self.kind
    }
}

/// The marks no name may contain: the one list every hygiene check uses.
///
/// Sources: `AGENTS.md` "Naming and Trademarks" (Arma, Operation Flashpoint, OFP, Cold War Assault/Crisis,
/// Resistance, Poseidon, Bohemia, the game's island names) and doc 02's naming checklist (which adds `Flashpoint`
/// alone and names the islands Everon, Malden, Kolgujev and Nogova). The islands' engine world names (`Eden`,
/// `Abel`, `Cain`, `Noe`; doc 04 §1) are what mission folders and configs use, so they are listed too.
///
/// Left out on purpose: `BI` (doc 02 lists it for product names, but a two-letter token matches ordinary words
/// such as `bi_directional`; the format family is named `lzss` in module names instead), the world names `Intro`
/// and `Demo` (ordinary words; `Intro` is also a mission type), and the profile ids `Cwa199`, `Cwr` and `Ce`
/// (owner-decided data values, D003, not names). Changing this list is a reviewed change to `AGENTS.md`'s rule.
pub const MARKS: &[Mark] = &[
    Mark::new("arma", MatchRule::Token, MarkKind::Trademark),
    Mark::new("flashpoint", MatchRule::Squashed, MarkKind::Trademark),
    Mark::new("ofp", MatchRule::TokenPrefix, MarkKind::Trademark),
    Mark::new("coldwarassault", MatchRule::Squashed, MarkKind::Trademark),
    Mark::new("coldwarcrisis", MatchRule::Squashed, MarkKind::Trademark),
    Mark::new("resistance", MatchRule::Token, MarkKind::Trademark),
    Mark::new("poseidon", MatchRule::Squashed, MarkKind::Trademark),
    Mark::new("bohemia", MatchRule::Squashed, MarkKind::Trademark),
    Mark::new("everon", MatchRule::Token, MarkKind::Island),
    Mark::new("malden", MatchRule::Token, MarkKind::Island),
    Mark::new("kolgujev", MatchRule::Squashed, MarkKind::Island),
    Mark::new("nogova", MatchRule::Squashed, MarkKind::Island),
    Mark::new("eden", MatchRule::Token, MarkKind::Island),
    Mark::new("abel", MatchRule::Token, MarkKind::Island),
    Mark::new("cain", MatchRule::Token, MarkKind::Island),
    Mark::new("noe", MatchRule::Token, MarkKind::Island),
];

/// What kind of name a [`NameSite`] holds, for messages.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum NameKind {
    /// A package name from `cargo metadata`.
    Crate,
    /// A build target name (library, binary, test, bench, example).
    Target,
    /// A file or folder name.
    Path,
    /// An inline `mod name` declaration.
    Module,
}

impl fmt::Display for NameKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::Crate => "crate name",
            Self::Target => "target name",
            Self::Path => "file or folder name",
            Self::Module => "module name",
        })
    }
}

/// One name to check, with where it was found.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct NameSite {
    kind: NameKind,
    location: String,
    name: String,
}

impl NameSite {
    /// A name of `kind` found at `location` (a path relative to the workspace root, with `:line` for modules).
    pub fn new(kind: NameKind, location: impl Into<String>, name: impl Into<String>) -> Self {
        Self {
            kind,
            location: location.into(),
            name: name.into(),
        }
    }
}

/// One name that breaks the naming rule.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Finding {
    /// The name contains a mark from [`MARKS`].
    Mark {
        /// Where the name was found.
        site: NameSite,
        /// The mark it contains.
        mark: Mark,
    },
    /// The name has characters outside printable ASCII, which could hide a mark.
    HiddenCharacters {
        /// Where the name was found.
        site: NameSite,
    },
}

impl fmt::Display for Finding {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Mark { site, mark } => {
                let what = match mark.kind() {
                    MarkKind::Trademark => "third-party mark",
                    MarkKind::Island => "island name",
                };
                write!(
                    f,
                    "{}: {} `{}` contains the {what} `{}`: rename it; the game is named only in descriptive text \
                     (AGENTS.md \"Naming and Trademarks\"; crate-map §15)",
                    display_name(&site.location),
                    site.kind,
                    display_name(&site.name),
                    mark.text()
                )
            }
            Self::HiddenCharacters { site } => write!(
                f,
                "{}: {} `{}` has characters outside printable ASCII, which can hide a mark from this check: rename \
                 it with ASCII letters, digits, '-', '_' and '.'",
                display_name(&site.location),
                site.kind,
                display_name(&site.name)
            ),
        }
    }
}

/// Lowercase tokens of `name`, from both splits (see the module docs), sorted and without duplicates.
pub fn tokens(name: &str) -> Vec<String> {
    let mut found = BTreeSet::new();
    for word in name
        .split(|c: char| !c.is_ascii_alphanumeric())
        .filter(|w| !w.is_empty())
    {
        let chars: Vec<char> = word.chars().collect();
        // Coarse split: letter/digit boundaries only, so `ArmA` stays one token.
        push_pieces(
            &chars,
            |prev, current, _| letter_digit_boundary(prev, current),
            &mut found,
        );
        // Fine split: also camel case, so `ArmaTools` and `OFPEditor` split.
        push_pieces(&chars, camel_boundary, &mut found);
    }
    found.into_iter().collect()
}

/// Whether a token boundary falls between `prev` and `current` for the coarse split.
fn letter_digit_boundary(prev: char, current: char) -> bool {
    prev.is_ascii_digit() != current.is_ascii_digit()
}

/// Whether a token boundary falls before `current` for the fine split: letter/digit changes, lower-to-upper
/// (`armA`), and the last capital of a capital run followed by a lowercase letter (`OFPEditor` -> `OFP`, `Editor`).
fn camel_boundary(prev: char, current: char, next: Option<char>) -> bool {
    letter_digit_boundary(prev, current)
        || (prev.is_ascii_lowercase() && current.is_ascii_uppercase())
        || (prev.is_ascii_uppercase()
            && current.is_ascii_uppercase()
            && next.is_some_and(|n| n.is_ascii_lowercase()))
}

/// Splits `chars` wherever `boundary(prev, current, next)` holds and adds each lowercase piece to `found`.
fn push_pieces(
    chars: &[char],
    boundary: impl Fn(char, char, Option<char>) -> bool,
    found: &mut BTreeSet<String>,
) {
    let mut piece = String::new();
    let mut prev: Option<char> = None;
    for (index, &current) in chars.iter().enumerate() {
        let next = chars.get(index.saturating_add(1)).copied();
        if let Some(p) = prev
            && boundary(p, current, next)
            && !piece.is_empty()
        {
            found.insert(std::mem::take(&mut piece));
        }
        piece.push(current.to_ascii_lowercase());
        prev = Some(current);
    }
    if !piece.is_empty() {
        found.insert(piece);
    }
}

/// The first mark in [`MARKS`] that `name` contains, if any.
pub fn find_mark(name: &str) -> Option<Mark> {
    let tokens = tokens(name);
    let squashed: String = name
        .chars()
        .filter(char::is_ascii_alphanumeric)
        .map(|c| c.to_ascii_lowercase())
        .collect();
    MARKS.iter().copied().find(|mark| match mark.rule {
        MatchRule::Token => tokens.iter().any(|t| t == mark.text),
        MatchRule::TokenPrefix => tokens.iter().any(|t| t.starts_with(mark.text)),
        MatchRule::Squashed => squashed.contains(mark.text),
    })
}

/// The inline `mod` declarations in Rust source, with their 1-based line numbers.
///
/// A line-based scan, not a parser: it sees `mod x;`, `mod x {`, `pub mod`, `pub(crate) mod`, `r#` names and
/// attributes on the same line, and skips comment lines. Good enough for names, which is all it is used for.
pub fn module_decls(source: &str) -> Vec<(usize, String)> {
    source
        .lines()
        .enumerate()
        .filter_map(|(index, line)| {
            module_decl(line).map(|name| (index.saturating_add(1), name.to_owned()))
        })
        .collect()
}

/// The module name declared on one line, if the line declares one.
fn module_decl(line: &str) -> Option<&str> {
    let mut rest = line.trim_start();
    // Attributes on the same line: `#[cfg(test)] mod tests;`.
    while let Some(attribute) = rest.strip_prefix("#[") {
        let close = attribute.find(']')?;
        rest = attribute.get(close.saturating_add(1)..)?.trim_start();
    }
    // Visibility: `pub`, `pub(crate)`, `pub(in path)`.
    if let Some(after_pub) = rest.strip_prefix("pub") {
        let after_pub = after_pub.trim_start();
        rest = match after_pub.strip_prefix('(') {
            Some(scope) => scope
                .get(scope.find(')')?.saturating_add(1)..)?
                .trim_start(),
            None => after_pub,
        };
    }
    let after_mod = rest.strip_prefix("mod")?;
    // `mod` must be a whole keyword (`modulo()` is not a declaration).
    if !after_mod.starts_with(char::is_whitespace) {
        return None;
    }
    let ident = after_mod.trim_start();
    let ident = ident.strip_prefix("r#").unwrap_or(ident);
    // Unicode identifiers are kept whole, so the character rule can report them.
    let end = ident
        .find(|c: char| !(c.is_alphanumeric() || c == '_'))
        .unwrap_or(ident.len());
    ident.get(..end).filter(|name| !name.is_empty())
}

/// The crate and target names of every workspace member, located by manifest path relative to the workspace root.
pub fn metadata_sites(metadata: &Metadata) -> Vec<NameSite> {
    let root = metadata.workspace_root();
    let mut sites = Vec::new();
    for member in metadata.members() {
        let location = relative_manifest(root, member.manifest_path());
        sites.push(NameSite::new(
            NameKind::Crate,
            location.clone(),
            member.name(),
        ));
        for target in member.targets() {
            sites.push(NameSite::new(
                NameKind::Target,
                location.clone(),
                target.name(),
            ));
        }
    }
    sites
}

/// A manifest path relative to the workspace root, with `/` separators (cargo prints native paths).
fn relative_manifest(root: &str, manifest_path: &str) -> String {
    let relative = manifest_path.strip_prefix(root).unwrap_or(manifest_path);
    relative
        .replace('\\', "/")
        .trim_start_matches('/')
        .to_owned()
}

/// Checks every site; returns the findings sorted and without duplicates.
#[must_use = "an unread report hides naming violations; print each finding and fail when the vector is not empty"]
pub fn check_sites(sites: &[NameSite]) -> Vec<Finding> {
    let mut found = BTreeSet::new();
    for site in sites {
        let printable = site.name.chars().all(|c| c == ' ' || c.is_ascii_graphic());
        if !printable {
            found.insert(Finding::HiddenCharacters { site: site.clone() });
        } else if let Some(mark) = find_mark(&site.name) {
            found.insert(Finding::Mark {
                site: site.clone(),
                mark,
            });
        }
    }
    found.into_iter().collect()
}

#[cfg(test)]
mod tests;
