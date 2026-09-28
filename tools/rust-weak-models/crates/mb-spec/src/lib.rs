//! Task specification shared by both API variants: catalogs, the `Refusal` enum and
//! one module per task holding its `Input` type. The prompt shows `catalog`,
//! `refusal` and the task's own module verbatim, identically for both variants.

pub mod catalog;
pub mod refusal;

pub use catalog::{Ending, Point, Radio, Rank, Side, UnitClass, UnitIn};
pub use refusal::{Problem, Refusal};

// ── Pilot tasks (never scored) ──
pub mod p01;
pub mod p02;
pub mod p03;
pub mod p04;

// ── Scored tasks ──
pub mod t01;
pub mod t02;
pub mod t03;
pub mod t04;
pub mod t05;
pub mod t06;
pub mod t07;
pub mod t08;
pub mod t09;
pub mod t10;
pub mod t11;
pub mod t12;
pub mod t13;
pub mod t14;
pub mod t15;
pub mod t16;
pub mod t17;
pub mod t18;
pub mod t19;
pub mod t20;
pub mod t21;
pub mod t22;
pub mod t23;
pub mod t24;
pub mod t25;
pub mod t26;
pub mod t27;
pub mod t28;
pub mod t29;
pub mod t30;
