pub fn f(label: &str) -> Result<(), spec::Refusal> { Err(spec::Refusal::OutOfMap(label.to_string())) }
pub fn g() -> Result<(), spec::Refusal> { let e = spec::Refusal::OutOfMap; Err(e) }
pub fn h(label: &str) -> spec::Refusal { spec::Refusal::TooFewWaypoints { what: label.to_string() } }
