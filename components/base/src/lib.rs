pub use serde_json::from_str as json_from_str;
pub use serde_json::json;
pub use serde_json::Value as JsonValue;

pub use std::collections::HashMap;
use std::error;
pub use std::ffi::{CStr, CString};
use std::fmt;
pub use std::mem::transmute;
pub use std::os::raw::{c_char, c_void};
pub use std::ptr::null_mut;
use std::slice::from_raw_parts_mut;
pub use std::vec::Vec;

// ===== generic error ===== //
#[derive(Debug)]
pub struct Error {
    msg: String,
}

impl Error {
    pub fn new(msg: String) -> Self {
        Self { msg }
    }
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

#[macro_export]
macro_rules! err {
    (box $($arg:tt)+) => {
        Box::new($crate::Error::new(format!($($arg)+)))
    };
    ($($arg:tt)+) => {
        Err($crate::err!(box $($arg)+))
    };
}

#[macro_export]
macro_rules! res {
    ($expr:expr) => {
        match $expr {
            Ok(t) => Ok(t),
            Err(e) => err!("{}", e.to_string()),
        }
    };
}

// ===== arg handling ===== //
pub fn args(body: &JsonValue) -> Result<&JsonValue, Box<Error>> {
    body.get("args").ok_or_else(|| err!(box "missing args"))
}

pub fn arg(body: &JsonValue, index: usize) -> Result<&JsonValue, Box<Error>> {
    args(body)?
        .get(index)
        .ok_or_else(|| err!(box "missing arg {}", index))
}

pub fn arg_str(body: &JsonValue, index: usize) -> Result<&str, Box<Error>> {
    arg(body, index)?
        .as_str()
        .ok_or_else(|| err!(box "arg {} isn't a string", index))
}

pub fn arg_num<T: std::str::FromStr>(body: &JsonValue, index: usize) -> Result<T, Box<Error>> {
    match arg_str(body, index)?.parse::<T>() {
        Ok(num) => Ok(num),
        Err(_) => err!("couldn't parse arg {} as appropriate number", index),
    }
}

pub fn kwargs(body: &JsonValue) -> Result<&JsonValue, Box<Error>> {
    body.get("kwargs").ok_or_else(|| err!(box "missing kwargs"))
}

pub fn kwarg<'a>(body: &'a JsonValue, name: &str) -> Result<&'a JsonValue, Box<Error>> {
    kwargs(body)?
        .get(name)
        .ok_or_else(|| err!(box "missing kwarg {}", name))
}

pub fn kwarg_str<'a>(body: &'a JsonValue, name: &str) -> Result<&'a str, Box<Error>> {
    kwarg(body, name)?
        .as_str()
        .ok_or_else(|| err!(box "kwarg {} isn't a string", name))
}

pub fn kwarg_num<T: std::str::FromStr>(body: &JsonValue, name: &str) -> Result<T, Box<Error>> {
    match kwarg_str(body, name)?.parse::<T>() {
        Ok(num) => Ok(num),
        Err(_) => err!("couldn't parse kwarg {} as appropriate number", name),
    }
}

pub fn json_get<'a>(value: &'a JsonValue, name: &str) -> Result<&'a JsonValue, Box<Error>> {
    value
        .get(name)
        .ok_or_else(|| err!(box "missing value {}", name))
}

pub fn json_str(value: &JsonValue) -> Result<&str, Box<Error>> {
    value
        .as_str()
        .ok_or_else(|| err!(box "expected a string, but didn't get one"))
}

pub fn json_num<T: std::str::FromStr>(value: &JsonValue) -> Result<T, Box<Error>> {
    match json_str(value)?.parse::<T>() {
        Ok(num) => Ok(num),
        Err(_) => err!("couldn't parse number"),
    }
}

#[macro_export]
macro_rules! marg {
    (args $body:expr) => {
        $crate::args($body)
    };
    (arg $body:expr, $index:expr) => {
        $crate::arg($body, $index)
    };
    (arg_str $body:expr, $index:expr) => {
        $crate::arg_str($body, $index)
    };
    (arg_num $body:expr, $index:expr) => {
        $crate::arg_num($body, $index)
    };
    (kwargs $body:expr) => {
        $crate::kwargs($body)
    };
    (kwarg $body:expr, $index:expr) => {
        $crate::kwarg($body, $index)
    };
    (kwarg_str $body:expr, $index:expr) => {
        $crate::kwarg_str($body, $index)
    };
    (kwarg_num $body:expr, $index:expr) => {
        $crate::kwarg_num($body, $index)
    };
    (json_get $json:expr, $name:expr) => {
        $crate::json_get($json, $name)
    };
    (json_str $json:expr) => {
        $crate::json_str($json)
    };
    (json_num $json:expr) => {
        $crate::json_num($json)
    };
}

// ===== views ===== //
pub const VIEW_ARGS: [&str; 5] = ["component", "command", "audio", "midi", "evaluate"];

pub type CommandView = extern "C" fn(*const c_void, *const c_char) -> *const c_char;
pub type MidiView = extern "C" fn(*const c_void, *const u8, usize);
pub type AudioView = extern "C" fn(*const c_void) -> *mut f32;
pub type EvaluateView = extern "C" fn(*const c_void);

#[derive(Debug, PartialEq)]
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
            None => return err!("pointer isn't a string"),
        };
        unsafe { transmute::<*const c_void, $type>(u as *const c_void) }
    }};
}

impl View {
    #[allow(clippy::useless_transmute)]
    pub fn new(args: &JsonValue) -> Result<Self, Box<dyn error::Error>> {
        Ok(Self {
            raw: json_to_ptr!(&args[0], *const c_void),
            command_view: json_to_ptr!(&args[1], CommandView),
            midi_view: json_to_ptr!(&args[2], MidiView),
            audio_view: json_to_ptr!(&args[3], AudioView),
            evaluate_view: json_to_ptr!(&args[4], EvaluateView),
        })
    }

    pub fn command(&self, body: &JsonValue) -> Option<JsonValue> {
        let text = CString::new(body.to_string()).expect("CString::new failed");
        let result = (self.command_view)(self.raw, text.as_ptr());
        if result.is_null() {
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
        if audio.is_null() {
            None
        } else {
            Some(unsafe { from_raw_parts_mut(audio, samples_per_evaluation) })
        }
    }

    pub fn evaluate(&self) {
        (self.evaluate_view)(self.raw);
    }
}

// ===== generate ===== //
#[macro_export]
macro_rules! gen_component {
    ($specifics:ident) => {
        gen_component!($specifics, {"in": ["?"], "out": ["?"]});
    };

    ($specifics:ident, $info:tt) => {
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
            pub func: Box<FnMut(&mut $specifics, $crate::JsonValue) -> Result<Option<$crate::JsonValue>, Box<dyn std::error::Error>>>,
            pub info: $crate::JsonValue,
        }

        pub type CommandMap = $crate::HashMap<&'static str, Command>;

        // ===== component ===== //
        pub struct Component {
            name: String,
            specifics: $specifics,
            result: $crate::CString,
            commands: CommandMap,
        }

        impl Component {
            fn set_result(&mut self, result: &str) -> *const $crate::c_char {
                self.result = $crate::CString::new(result).expect("CString::new failed");
                self.result.as_ptr()
            }
        }

        impl std::fmt::Debug for Component {
            fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                f.debug_struct("Component")
                    .field("name", &self.name)
                    .finish()
            }
        }

        // ===== external functions ===== //
        #[no_mangle]
        pub extern "C" fn construct(name: *const $crate::c_char) -> *mut Component {
            let name = unsafe { $crate::CStr::from_ptr(name) }.to_str().expect("CStr::to_str failed");
            let mut component = Component {
                name: name.to_string(),
                specifics: $specifics::new(),
                result: $crate::CString::new("").expect("CString::new failed"),
                commands: CommandMap::new(),
            };
            component.specifics.register_commands(&mut component.commands);
            // info
            component.commands.insert(
                "info",
                Command {
                    func: Box::new(|_soul, _body| {
                        Ok(Some($crate::json!($info)))
                    }),
                    info: $crate::json!({}),
                },
            );
            // join
            if !component.commands.contains_key("join") {
                component.commands.insert(
                    "join",
                    Command {
                        func: Box::new(|_soul, _body| {
                            Ok(None)
                        }),
                        info: $crate::json!({}),
                    },
                );
            }
            // midi
            if !component.commands.contains_key("midi") {
                component.commands.insert(
                    "midi",
                    Command {
                        func: Box::new(move |soul, body| {
                            let arr = $crate::arg(&body, 0)?.as_array().ok_or_else(|| $crate::err!(box "msg isn't an array"))?;
                            if arr.len() <= 3 {
                                let mut slice = [0 as u8; 3];
                                for i in 0..arr.len() {
                                    slice[i] = arr[i].as_str().ok_or_else(|| $crate::err!(box "msg element isn't a str"))?.parse::<u8>()?;
                                }
                                soul.midi(&slice);
                            } else {
                                let mut vec = Vec::<u8>::new();
                                for i in arr {
                                    vec.push(i.as_str().ok_or_else(|| $crate::err!(box "msg element isn't a str"))?.parse::<u8>()?);
                                }
                                soul.midi(vec.as_slice());
                            }
                            Ok(None)
                        }),
                        info: $crate::json!({
                            "args": ["msg"],
                        }),
                    },
                );
            }
            // list
            let mut list: $crate::Vec<$crate::JsonValue> = Default::default();
            for (name, command) in &component.commands {
                list.push($crate::json!({
                    "name": name,
                    "info": command.info,
                }));
            }
            list.push($crate::json!({"name": "list", "info": {}}));
            list.sort_by_key(|i| {
                match i["name"].as_str().unwrap() {
                    "info" => "~0",
                    "list" => "~1",
                    "join" => "~2",
                    "connect" => "~3",
                    "disconnect" => "~4",
                    "midi" => "~5",
                    "to_json" => "~6",
                    "from_json" => "~7",
                    name => name,
                }.to_string()
            });
            component.commands.insert(
                "list",
                Command {
                    func: Box::new(move |soul, _body| {
                        Ok(Some($crate::json!(list)))
                    }),
                    info: $crate::json!({}),
                },
            );
            // done
            Box::into_raw(Box::new(component))
        }

        #[no_mangle]
        pub extern "C" fn destruct(component: *mut Component) {
            unsafe { Box::from_raw(component) };
        }

        #[no_mangle]
        pub extern "C" fn command(component: *mut Component, text: *const $crate::c_char) -> *const $crate::c_char {
            let component = unsafe { &mut *component };
            let text = unsafe { $crate::CStr::from_ptr(text) }.to_str().expect("CStr::to_str failed");
            if std::option_env!("DLAL_SNOOP_COMMAND").is_some() {
                println!("{:?} command {:02x?}", component, text);
            }
            let body: $crate::JsonValue = match $crate::json_from_str(text) {
                Ok(body) => body,
                Err(err) => return component.set_result(&$crate::json!({"error": err.to_string()}).to_string()),
            };
            let name = match body["name"].as_str() {
                Some(name) => name,
                None => return component.set_result(&$crate::json!({"error": "command name isn't a string"}).to_string()),
            };
            let command = match component.commands.get_mut(name) {
                Some(command) => command,
                None => return component.set_result(&$crate::json!({"error": format!(r#"no such command "{}""#, name)}).to_string()),
            };
            match (command.func)(&mut component.specifics, body) {
                Ok(result) => match(result) {
                    Some(result) => component.set_result(&result.to_string()),
                    None => std::ptr::null(),
                },
                Err(err) => component.set_result(&$crate::json!({"error": err.to_string()}).to_string()),
            }
        }

        #[no_mangle]
        pub extern "C" fn midi(component: *mut Component, msg: *const u8, size: usize) {
            let component = unsafe { &mut *component };
            let msg = unsafe { std::slice::from_raw_parts(msg, size) };
            if std::option_env!("DLAL_SNOOP_MIDI").is_some() {
                println!("{:?} midi {:02x?}", component, msg);
            }
            component.specifics.midi(msg);
        }

        #[no_mangle]
        pub extern "C" fn audio(component: *mut Component) -> *mut f32 {
            let component = unsafe { &mut *component };
            match component.specifics.audio() {
                Some(audio) => audio.as_mut_ptr(),
                None => $crate::null_mut(),
            }
        }

        #[no_mangle]
        pub extern "C" fn evaluate(component: *mut Component) {
            let component = unsafe { &mut *component };
            if let Some(percent) = std::option_env!("DLAL_SNOOP_AUDIO") {
                let audio = audio(component);
                if audio != $crate::null_mut() {
                    use std::time::{SystemTime, UNIX_EPOCH};
                    let timestamp = SystemTime::now()
                        .duration_since(UNIX_EPOCH)
                        .expect("duration_since failed")
                        .as_millis();
                    let percent = percent.parse::<u8>()
                        .expect(&format!("couldn't parse DLAL_SNOOP_AUDIO={} as u8", percent));
                    if (timestamp % 100 < percent as u128) {
                        println!("{:?} audio {}", component, unsafe { *audio });
                    }
                }
            }
            component.specifics.evaluate();
        }
    };
}

#[macro_export]
macro_rules! command {
    ($commands:expr, $name:expr, $func:expr, $info:tt$(,)?) => {
        $commands.insert(
            $name,
            Command {
                func: Box::new($func),
                info: $crate::json!($info),
            },
        );
    };
}

#[macro_export]
macro_rules! join {
    ($commands:expr, $func:expr, $kwargs:tt$(,)?) => {
        $crate::command!(
            $commands,
            "join",
            $func,
            {
                "kwargs": $kwargs,
            },
        );
    };
    (samples_per_evaluation $soul:ident, $body:ident) => {
        $soul.samples_per_evaluation = $crate::kwarg_num(&$body, "samples_per_evaluation")?;
    };
    (sample_rate $soul:ident, $body:ident) => {
        $soul.sample_rate = $crate::kwarg_num(&$body, "sample_rate")?;
    };
}

#[macro_export]
macro_rules! uni {
    (connect $commands:expr, $check_audio:expr) => {
        command!(
            $commands,
            "connect",
            |soul, body| {
                let output = $crate::View::new($crate::args(&body)?)?;
                if $check_audio && output.audio(0) == None {
                    return $crate::err!("output must have audio");
                }
                soul.output = Some(output);
                Ok(None)
            },
            { "args": $crate::VIEW_ARGS },
        );
        command!(
            $commands,
            "disconnect",
            |soul, body| {
                let output = View::new($crate::args(&body)?)?;
                if soul.output == Some(output) {
                    soul.output = None;
                }
                Ok(None)
            },
            {},
        );
    };
}

#[macro_export]
macro_rules! multi {
    (connect $commands:expr, $check_audio:expr) => {
        $crate::command!(
            $commands,
            "connect",
            |soul, body| {
                let output = $crate::View::new($crate::args(&body)?)?;
                if $check_audio && output.audio(0) == None {
                    return $crate::err!("output must have audio");
                }
                soul.outputs.push(output);
                Ok(None)
            },
            { "args": $crate::VIEW_ARGS },
        );
        $crate::command!(
            $commands,
            "disconnect",
            |soul, body| {
                let output = $crate::View::new($crate::args(&body)?)?;
                if let Some(i) = soul.outputs.iter().position(|i| i == &output) {
                    soul.outputs.remove(i);
                }
                Ok(None)
            },
            { "args": $crate::VIEW_ARGS },
        );
    };
    (midi $msg:expr, $outputs:expr) => {
        for output in &$outputs {
            output.midi(&$msg);
        }
    };
    (audio $audio:expr, $outputs:expr, $samples_per_evaluation:expr) => {
        for output in &$outputs {
            let audio = output.audio($samples_per_evaluation).unwrap();
            for i in 0..$samples_per_evaluation {
                audio[i] += $audio[i];
            }
        }
    };
}
