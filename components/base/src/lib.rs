pub use serde_json::from_str as json_from_str;
pub use serde_json::json;
pub use serde_json::Value as JsonValue;

use std::error;
use std::ffi::{CStr, CString};
use std::fmt;
use std::mem::transmute;
use std::os::raw::{c_char, c_void};
use std::ptr::null;

#[derive(Debug)]
pub struct Error {
    msg: String,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.msg)
    }
}

impl std::error::Error for Error {
    fn description(&self) -> &str {
        &self.msg
    }

    fn cause(&self) -> Option<&(dyn std::error::Error)> {
        None
    }
}

pub fn err(msg: &str) -> Box<Error> {
    Box::new(Error {
        msg: msg.to_string(),
    })
}

#[macro_export]
macro_rules! gen_component {
    ($specifics:ident) => {
        pub struct Command {
            pub func: fn(&mut $specifics, dlal_base::JsonValue) -> Result<Option<dlal_base::JsonValue>, Box<dyn std::error::Error>>,
            pub info: dlal_base::JsonValue,
        }

        pub type CommandMap = std::collections::HashMap<&'static str, Command>;

        pub struct Component {
            specifics: $specifics,
            result: std::ffi::CString,
            commands: CommandMap,
        }

        impl Component {
            fn set_result(&mut self, result: &str) -> *const std::os::raw::c_char {
                self.result = std::ffi::CString::new(result).expect("CString::new failed");
                self.result.as_ptr()
            }
        }

        #[no_mangle]
        pub extern "C" fn construct() -> *mut Component {
            let mut component = Component {
                specifics: $specifics::new(),
                result: std::ffi::CString::new("").expect("CString::new failed"),
                commands: CommandMap::new(),
            };
            component.specifics.register_commands(&mut component.commands);
            Box::into_raw(Box::new(component))
        }

        #[no_mangle]
        pub extern "C" fn destruct(component: *mut Component) {
            unsafe { Box::from_raw(component) };
        }

        #[no_mangle]
        pub extern "C" fn command(component: *mut Component, text: *const std::os::raw::c_char) -> *const std::os::raw::c_char {
            let component = unsafe { &mut *component };
            let text = unsafe { std::ffi::CStr::from_ptr(text) }.to_str().expect("CStr::to_str failed");
            let body: dlal_base::JsonValue = match dlal_base::json_from_str(text) {
                Ok(body) => body,
                Err(err) => return component.set_result(&json!({"error": err.to_string()}).to_string()),
            };
            let name = match body["name"].as_str() {
                Some(name) => name,
                None => return component.set_result(&json!({"error": "command name isn't a string"}).to_string()),
            };
            let command = match component.commands.get(name) {
                Some(command) => command,
                None => return component.set_result(&json!({"error": format!(r#"no such command "{}""#, name)}).to_string()),
            };
            match (command.func)(&mut component.specifics, body) {
                Ok(result) => match(result) {
                    Some(result) => component.set_result(&result.to_string()),
                    None => std::ptr::null(),
                },
                Err(err) => component.set_result(&json!({"error": err.to_string()}).to_string()),
            }
        }

        #[no_mangle]
        pub extern "C" fn evaluate(component: *mut Component) {
            let component = unsafe { &mut *component };
            component.specifics.evaluate();
        }
    }
}

pub type CommandView = extern "C" fn(*const c_void, *const c_char) -> *const c_char;
pub type MidiView = extern "C" fn(*const c_void, *const u8, usize);
pub type AudioView = extern "C" fn(*const c_void) -> *mut f32;
pub type EvaluateView = extern "C" fn(*const c_void);

pub struct ComponentView {
    raw: *const c_void,
    command_view: Option<CommandView>,
    midi_view: Option<MidiView>,
    audio_view: Option<AudioView>,
    evaluate_view: Option<EvaluateView>,
}

macro_rules! json_to_ptr {
    ($value:expr, $type:ty) => {{
        let u = match $value.as_str() {
            Some(s) => s.parse::<usize>()?,
            None => return Err(err("pointer isn't a string")),
        };
        unsafe { transmute::<usize, $type>(u) }
    }};
}

macro_rules! json_to_ptr_opt {
    ($value:expr, $type:ty) => {{
        if $value.is_null() {
            None
        } else {
            Some(json_to_ptr!($value, $type))
        }
    }};
}

impl ComponentView {
    pub fn new(args: &JsonValue) -> Result<Self, Box<dyn error::Error>> {
        Ok(Self {
            raw: json_to_ptr!(&args[0], *const c_void),
            command_view: json_to_ptr_opt!(&args[1], CommandView),
            midi_view: json_to_ptr_opt!(&args[2], MidiView),
            audio_view: json_to_ptr_opt!(&args[3], AudioView),
            evaluate_view: json_to_ptr_opt!(&args[4], EvaluateView),
        })
    }

    pub fn command(&self, body: JsonValue) -> Option<JsonValue> {
        let result = self.command_view.unwrap()(
            self.raw,
            CString::new(body.to_string())
                .expect("CString::new failed")
                .as_ptr(),
        );
        if result == null() {
            return None;
        }
        let result = unsafe { CStr::from_ptr(result) }
            .to_str()
            .expect("CStr::to_str failed");
        Some(json_from_str(result).expect("invalid result"))
    }

    pub fn midi(&self) {
        self.midi_view;
    }

    pub fn audio(&self) {
        self.audio_view;
    }

    pub fn evaluate(&self) {
        self.evaluate_view.unwrap()(self.raw);
    }
}
