//! Trigger areas, activations, timers and the typestate `TriggerBuilder`.

use std::fmt;
use std::marker::PhantomData;

use mb_core as core;
use mb_spec::{Ending, Radio, Side};

use crate::measure::{Degrees, Metres, Pos, Seconds};
use crate::sealed::Sealed;

/// Rectangular trigger area: centre, half sizes `a` (east-west) and `b`
/// (north-south), rotated by `angle`.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Area {
    pub(crate) centre: Pos,
    pub(crate) a: Metres,
    pub(crate) b: Metres,
    pub(crate) angle: Degrees,
}

impl Area {
    /// An area around `centre`.
    pub fn new(centre: Pos, a: Metres, b: Metres, angle: Degrees) -> Area {
        Area { centre, a, b, angle }
    }

    /// An area covering the whole map.
    pub fn whole_map() -> Area {
        let half = core::MAP_SIZE / 2.0;
        Area {
            // The map centre is on the map by definition, so the unchecked constructor is sound.
            centre: Pos::on_map_unchecked(half, half),
            a: Metres::new(half),
            b: Metres::new(half),
            angle: Degrees::new(0.0),
        }
    }
}

/// Error: a side cannot detect itself (rule R7).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SameSide {
    pub side: Side,
}

impl fmt::Display for SameSide {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:?} cannot detect itself", self.side)
    }
}

impl std::error::Error for SameSide {}

/// Condition that activates a trigger. Build it with one of the constructors.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Activation(pub(crate) core::Act);

impl Activation {
    /// No condition (for example a trigger that only waits for its timer or a sync).
    pub fn none() -> Activation {
        Activation(core::Act::None)
    }

    /// Fires when units of `side` are in the area.
    pub fn present(side: Side) -> Activation {
        Activation(core::Act::Present(side))
    }

    /// Fires when no units of `side` are in the area.
    pub fn not_present(side: Side) -> Activation {
        Activation(core::Act::NotPresent(side))
    }

    /// Fires when the player calls the radio `channel`.
    pub fn radio(channel: Radio) -> Activation {
        Activation(core::Act::Radio(channel))
    }

    /// Fires when `detected` is detected by `detector` in the area; reads as
    /// "`detected` detected by `detector`". Errors with `SameSide` if both are equal.
    pub fn detected_by(detected: Side, detector: Side) -> Result<Activation, SameSide> {
        if detected == detector {
            return Err(SameSide { side: detector });
        }
        Ok(Activation(core::Act::DetectedBy { detector, detected }))
    }
}

/// Error: timer values must satisfy `0 <= min <= mid <= max` (rule R6).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct TimerOrder {
    pub min: Seconds,
    pub mid: Seconds,
    pub max: Seconds,
}

impl fmt::Display for TimerOrder {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "timer {}/{}/{} s is not 0 <= min <= mid <= max", self.min.get(), self.mid.get(), self.max.get())
    }
}

impl std::error::Error for TimerOrder {}

/// A checked trigger timer. `mid` is the typical delay.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Timer(pub(crate) core::Timer);

impl Timer {
    /// Countdown: fires `min..max` seconds after the condition became true.
    /// Convert minutes with `Seconds::from_minutes`. Errors with `TimerOrder`.
    pub fn countdown(min: Seconds, mid: Seconds, max: Seconds) -> Result<Timer, TimerOrder> {
        Timer::checked(core::TimerKind::Countdown, min, mid, max)
    }

    /// Timeout: fires once the condition stayed true for `min..max` seconds.
    /// Convert minutes with `Seconds::from_minutes`. Errors with `TimerOrder`.
    pub fn timeout(min: Seconds, mid: Seconds, max: Seconds) -> Result<Timer, TimerOrder> {
        Timer::checked(core::TimerKind::Timeout, min, mid, max)
    }

    fn checked(kind: core::TimerKind, min: Seconds, mid: Seconds, max: Seconds) -> Result<Timer, TimerOrder> {
        let (lo, md, hi) = (min.get(), mid.get(), max.get());
        if lo <= md && md <= hi && lo >= 0.0 {
            Ok(Timer(core::Timer { kind, min: lo, mid: md, max: hi }))
        } else {
            Err(TimerOrder { min, mid, max })
        }
    }
}

/// Builder state: no activation chosen yet.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct NeedsActivation;
/// Builder state: activation chosen; the trigger can be added.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Ready;
/// Builder state: fires once and has no END/LOSE effect yet (the default).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Once;
/// Builder state: fires repeatedly; cannot end or lose the mission.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Repeating;
/// Builder state: fires once and ends (or loses) the mission; cannot repeat.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Ends;

impl Sealed for NeedsActivation {}
impl Sealed for Ready {}
impl Sealed for Once {}
impl Sealed for Repeating {}
impl Sealed for Ends {}

/// Builder states with an activation: `Ready`.
#[diagnostic::on_unimplemented(
    message = "this trigger has no activation yet (state `{Self}`)",
    label = "activation missing",
    note = "fix: call `.activation(Activation::...)` before `add_trigger`; use `Activation::none()` for a trigger without a condition"
)]
pub trait ActivationSet: Sealed {}
impl ActivationSet for Ready {}

/// Builder states that may fire repeatedly: `Once`, `Repeating`.
#[diagnostic::on_unimplemented(
    message = "an END or LOSE trigger cannot repeat (state `{Self}`)",
    label = "this trigger already ends the mission",
    note = "fix: END and LOSE triggers always fire once (rule R8): drop `.repeating()`"
)]
pub trait MayRepeat: Sealed {}
impl MayRepeat for Once {}
impl MayRepeat for Repeating {}

/// Builder states that fire once: `Once`, `Ends`.
#[diagnostic::on_unimplemented(
    message = "a repeating trigger cannot end or lose the mission (state `{Self}`)",
    label = "this trigger repeats",
    note = "fix: END and LOSE triggers must fire once (rule R8): remove `.repeating()`"
)]
pub trait FiresOnce: Sealed {}
impl FiresOnce for Once {}
impl FiresOnce for Ends {}

/// Builds a trigger step by step: `TriggerBuilder::new(area)`, then
/// `.activation(..)` (required), then optionally `.repeating()`, `.timer(..)`,
/// `.ends_mission(..)` or `.loses_mission()`; finally `Mission::add_trigger`.
/// A new trigger fires once.
#[derive(Debug, Clone, PartialEq)]
pub struct TriggerBuilder<A = NeedsActivation, R = Once> {
    pub(crate) area: Area,
    pub(crate) act: core::Act,
    pub(crate) repeating: bool,
    pub(crate) timer: Option<Timer>,
    pub(crate) effect: core::Effect,
    _state: PhantomData<(A, R)>,
}

impl TriggerBuilder<NeedsActivation, Once> {
    /// Starts a trigger over `area`; next call `.activation(..)`.
    pub fn new(area: Area) -> TriggerBuilder<NeedsActivation, Once> {
        TriggerBuilder {
            area,
            act: core::Act::None,
            repeating: false,
            timer: None,
            effect: core::Effect::None,
            _state: PhantomData,
        }
    }
}

impl<A, R> TriggerBuilder<A, R> {
    fn to<A2, R2>(self) -> TriggerBuilder<A2, R2> {
        TriggerBuilder {
            area: self.area,
            act: self.act,
            repeating: self.repeating,
            timer: self.timer,
            effect: self.effect,
            _state: PhantomData,
        }
    }

    /// Sets the activation condition.
    pub fn activation(mut self, activation: Activation) -> TriggerBuilder<Ready, R> {
        self.act = activation.0;
        self.to()
    }

    /// Lets the trigger fire again each time its condition becomes true.
    pub fn repeating(mut self) -> TriggerBuilder<A, Repeating>
    where
        R: MayRepeat,
    {
        self.repeating = true;
        self.to()
    }

    /// Adds a timer (build it with `Timer::countdown` or `Timer::timeout`).
    pub fn timer(mut self, timer: Timer) -> TriggerBuilder<A, R> {
        self.timer = Some(timer);
        self
    }

    /// Makes the trigger end the mission with `ending`. Only for triggers that fire once.
    pub fn ends_mission(mut self, ending: Ending) -> TriggerBuilder<A, Ends>
    where
        R: FiresOnce,
    {
        self.effect = core::Effect::End(ending);
        self.to()
    }

    /// Makes the trigger lose the mission. Only for triggers that fire once.
    pub fn loses_mission(mut self) -> TriggerBuilder<A, Ends>
    where
        R: FiresOnce,
    {
        self.effect = core::Effect::Lose;
        self.to()
    }
}
