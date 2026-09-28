#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Refusal { OutOfMap, TooFewWaypoints, Many(Vec<u8>) }
