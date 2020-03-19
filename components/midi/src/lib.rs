use midir::{MidiInput, MidiInputConnection};
use serde_json::{Value};

use std::ffi::{CStr, CString};
use std::os::raw::c_char;

fn new_midi_in() -> MidiInput {
    MidiInput::new("midir test input").expect("MidiInput::new failed")
}

pub struct Component {
    conn: Option<MidiInputConnection<()>>,
    result: CString,
}

impl Component {
    fn get_ports(&self) -> Vec<String> {
        let midi_in = new_midi_in();
        (0..midi_in.port_count()).map(|i| midi_in.port_name(i).expect("port_name failed")).collect()
    }

    fn open(&mut self, port: usize) {
        let midi_in = new_midi_in();
        self.conn = Some(midi_in.connect(
            port,
            "dlal-midir-input",
            move |_timestamp_us, message, _data| {
                println!("{:?}", message);
            },
            (),
        ).expect("MidiIn::connect failed"));
    }

    fn set_result(&mut self, new_result: &str) -> *const c_char {
        self.result = CString::new(new_result).expect("CString::new failed");
        self.result.as_ptr()
    }
}

#[no_mangle]
pub extern "C" fn construct() -> *mut Component {
    Box::into_raw(Box::new(Component {
        conn: None,
        result: CString::new("").expect("CString::new failed"),
    }))
}

#[no_mangle]
pub extern "C" fn destruct(component: *mut Component) {
    unsafe { Box::from_raw(component) };
}

#[no_mangle]
pub extern "C" fn command(component: *mut Component, text: *const c_char) -> *const c_char {
    let component = unsafe { &mut *component };
    let body: Value = serde_json::from_str(unsafe { CStr::from_ptr(text) }.to_str().expect("CStr::to_str failed")).expect("invalid command");
    match body["name"].as_str().expect("command name isn't a string") {
        "ports" => {
            let ports = component.get_ports();
            component.set_result(&serde_json::to_string(&ports).expect("serde_json::to_string failed"))
        },
        "open" => {
            let port = body["args"][0].as_str().expect("port isn't a string");
            let ports = component.get_ports();
            for (i, v) in ports.iter().enumerate() {
                if v.starts_with(port) {
                    component.open(i);
                    return std::ptr::null();
                }
            }
            component.set_result(r#"{"error": "no such port"}"#)
        },
        _ => {
            component.set_result(r#"{"error": "no such command"}"#)
        },
    }
}
