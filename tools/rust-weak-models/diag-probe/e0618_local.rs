#[derive(Debug)]
pub enum Refusal { OutOfMap }
pub fn f(label: &str) -> Result<(), Refusal> { Err(Refusal::OutOfMap(label.to_string())) }
