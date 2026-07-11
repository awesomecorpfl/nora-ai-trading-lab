//! Phase 1 reservation of the locked file/subprocess boundary; no research logic.
use std::{env, fs};
fn main() {
    let path = env::args().nth(1).expect("usage: labengine <task.json>");
    let spec = fs::read_to_string(path).expect("read task spec");
    assert!(spec.trim_start().starts_with('{'), "task spec must be JSON object");
    println!("{{\"phase\":1,\"accepted_task_spec\":true}}");
}
