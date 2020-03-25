pub use serde_json::from_str as json_from_str;
pub use serde_json::json;
pub use serde_json::Value as JsonValue;

use std::error;
use std::ffi::{CStr, CString};
use std::fmt;
use std::mem::transmute;
use std::os::raw::{c_char, c_void};
use std::ptr::{null, null_mut};
use std::slice::from_raw_parts_mut;

// ===== generic error ===== //
#[derive(Debug)]
pub struct Error {
    msg: String,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.msg)
    }
}

impl error::Error for Error {
    fn description(&self) -> &str {
        &self.msg
    }

    fn cause(&self) -> Option<&(dyn error::Error)> {
        None
    }
}

pub fn err(msg: &str) -> Box<Error> {
    Box::new(Error {
        msg: msg.to_string(),
    })
}

// ===== arg handling ===== //
pub fn args(body: &JsonValue) -> Result<&JsonValue, Box<Error>> {
    body.get("args").ok_or(err("missing args"))
}

pub fn arg(body: &JsonValue, index: usize) -> Result<&JsonValue, Box<Error>> {
    args(body)?
        .get(index)
        .ok_or(err(&format!("missing arg {}", index)))
}

pub fn arg_str(body: &JsonValue, index: usize) -> Result<&str, Box<Error>> {
    arg(body, index)?
        .as_str()
        .ok_or(err(&format!("arg {} isn't a string", index)))
}

pub fn arg_num<T: std::str::FromStr>(body: &JsonValue, index: usize) -> Result<T, Box<Error>> {
    match arg_str(body, index)?.parse::<T>() {
        Ok(num) => Ok(num),
        Err(_) => Err(err(&format!(
            "couldn't parse arg {} as appropriate number",
            index
        ))),
    }
}

pub fn kwargs(body: &JsonValue) -> Result<&JsonValue, Box<Error>> {
    body.get("kwargs").ok_or(err("missing kwargs"))
}

pub fn kwarg<'a>(body: &'a JsonValue, name: &str) -> Result<&'a JsonValue, Box<Error>> {
    kwargs(body)?
        .get(name)
        .ok_or(err(&format!("missing kwarg {}", name)))
}

pub fn kwarg_str<'a>(body: &'a JsonValue, name: &str) -> Result<&'a str, Box<Error>> {
    kwarg(body, name)?
        .as_str()
        .ok_or(err(&format!("kwarg {} isn't a string", name)))
}

pub fn kwarg_num<T: std::str::FromStr>(body: &JsonValue, name: &str) -> Result<T, Box<Error>> {
    match kwarg_str(body, name)?.parse::<T>() {
        Ok(num) => Ok(num),
        Err(_) => Err(err(&format!(
            "couldn't parse kwarg {} as appropriate number",
            name
        ))),
    }
}

// ===== views ===== //
pub const VIEW_ARGS: [&str; 5] = ["component", "command", "audio", "midi", "evaluate"];

pub type CommandView = extern "C" fn(*const c_void, *const c_char) -> *const c_char;
pub type MidiView = extern "C" fn(*const c_void, *const u8, usize);
pub type AudioView = extern "C" fn(*const c_void) -> *mut f32;
pub type EvaluateView = extern "C" fn(*const c_void);

pub struct View {
    raw: *const c_void,
    command_view: CommandView,
    midi_view: MidiView,
    audio_view: AudioView,
    evaluate_view: EvaluateView,
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

impl View {
    pub fn new(args: &JsonValue) -> Result<Self, Box<dyn error::Error>> {
        Ok(Self {
            raw: json_to_ptr!(&args[0], *const c_void),
            command_view: json_to_ptr!(&args[1], CommandView),
            midi_view: json_to_ptr!(&args[2], MidiView),
            audio_view: json_to_ptr!(&args[3], AudioView),
            evaluate_view: json_to_ptr!(&args[4], EvaluateView),
        })
    }

    pub fn command(&self, body: JsonValue) -> Option<JsonValue> {
        let result = (self.command_view)(
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

    pub fn midi(&self, msg: &[u8]) {
        (self.midi_view)(self.raw, msg.as_ptr(), msg.len());
    }

    pub fn audio(&self, samples_per_evaluation: usize) -> Option<&mut [f32]> {
        let audio = (self.audio_view)(self.raw);
        return if audio == null_mut() {
            None
        } else {
            Some(unsafe { from_raw_parts_mut(audio, samples_per_evaluation) })
        };
    }

    pub fn evaluate(&self) {
        (self.evaluate_view)(self.raw);
    }
}

// ===== generate ===== //
#[macro_export]
macro_rules! gen_component {
    ($specifics:ident) => {
        // ===== specifics trait ===== //
        pub trait SpecificsTrait {
            fn new() -> Self;
            fn register_commands(&self, commands: &mut CommandMap) {}
            fn evaluate(&mut self) {}
            fn midi(&mut self, _msg: &[u8]) {}
            fn audio(&mut self) -> Option<&mut[f32]> { None }
        }

        // ===== commands ===== //
        pub struct Command {
            pub func: fn(&mut $specifics, dlal_component_base::JsonValue) -> Result<Option<dlal_component_base::JsonValue>, Box<dyn std::error::Error>>,
            pub info: dlal_component_base::JsonValue,
        }

        pub type CommandMap = std::collections::HashMap<&'static str, Command>;

        // ===== component ===== //
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

        // ===== external functions ===== //
        #[no_mangle]
        pub extern "C" fn construct() -> *mut Component {
            let mut component = Component {
                specifics: $specifics::new(),
                result: std::ffi::CString::new("").expect("CString::new failed"),
                commands: CommandMap::new(),
            };
            component.specifics.register_commands(&mut component.commands);
            if !component.commands.contains_key("join") {
                component.commands.insert(
                    "join",
                    Command {
                        func: |_soul, _body| {
                            Ok(None)
                        },
                        info: json!({}),
                    },
                );
            }
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
            let body: dlal_component_base::JsonValue = match dlal_component_base::json_from_str(text) {
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
        pub extern "C" fn midi(component: *mut Component, msg: *const u8, size: usize) {
            let component = unsafe { &mut *component };
            component.specifics.midi(unsafe { std::slice::from_raw_parts(msg, size) });
        }

        #[no_mangle]
        pub extern "C" fn audio(component: *mut Component) -> *mut f32 {
            let component = unsafe { &mut *component };
            match component.specifics.audio() {
                Some(audio) => audio.as_mut_ptr(),
                None => std::ptr::null_mut(),
            }
        }

        #[no_mangle]
        pub extern "C" fn evaluate(component: *mut Component) {
            let component = unsafe { &mut *component };
            component.specifics.evaluate();
        }
    }
}