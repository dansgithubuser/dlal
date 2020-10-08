pub use serde_json;
pub use serde_json::json;

use std::any::type_name;
pub use std::collections::HashMap;
use std::error::Error as StdError;
pub use std::ffi::{CStr, CString};
use std::fmt;
pub use std::mem::transmute;
pub use std::os::raw::{c_char, c_void};
pub use std::ptr::null_mut;
use std::slice::from_raw_parts_mut;

// ===== generic error ===== //
#[derive(Debug)]
pub struct Error {
    msg: String,
}

impl Error {
    pub fn new(msg: &str) -> Self {
        Self { msg: msg.into() }
    }

    pub fn err<T>(msg: &str) -> Result<T, Self> {
        Err(Self::new(msg))
    }
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.msg)
    }
}

impl StdError for Error {
    fn description(&self) -> &str {
        &self.msg
    }

    fn cause(&self) -> Option<&(dyn StdError)> {
        None
    }
}

// ===== arg handling ===== //
// ----- Arg ------ //
pub trait Arg {
    fn from_value(value: &serde_json::Value) -> Option<Self> where Self: Sized;

    fn vec_map<B, F>(self, f: F) -> Result<Vec<B>, Box<dyn StdError>>
    where
        Self: Sized,
        Self: IntoIterator,
        F: FnMut(<Self as IntoIterator>::Item) -> Result<B, Box<dyn StdError>>,
    {
        self.into_iter().map(f).collect()
    }

    fn vec<T: Arg>(self) -> Result<Vec<T>, Box<dyn StdError>>
    where
        Self: Sized,
        Self: IntoIterator,
        <Self as IntoIterator>::Item: Body,
    {
        self.vec_map(|i| Ok(i.to()?))
    }
}

// ----- Arg impls ----- //
impl Arg for String {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        value.as_str().map(|i| i.into())
    }
}

impl Arg for f64 {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        value.as_f64()
    }
}

impl Arg for f32 {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        value.as_f64().map(|i| i as f32)
    }
}

impl Arg for i32 {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        value.as_i64().map(|i| i as i32)
    }
}

impl Arg for u64 {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        value.as_u64()
    }
}

impl Arg for u32 {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        value.as_u64().map(|i| i as u32)
    }
}

impl Arg for u8 {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        value.as_u64().map(|i| i as u8)
    }
}

impl Arg for usize {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        value.as_u64().map(|i| i as usize)
    }
}

impl Arg for bool {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        value.as_bool()
    }
}

impl Arg for Vec<serde_json::Value> {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        value.as_array().map(|i| i.clone())
    }
}

impl Arg for serde_json::Map<String, serde_json::Value> {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        value.as_object().map(|i| i.clone())
    }
}

impl Arg for serde_json::Value {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        Some(value.clone())
    }
}

// ----- Body ----- //
pub trait Body {
    fn arg<T: Arg>(&self, index: usize) -> Result<T, Error>;
    fn kwarg<T: Arg>(&self, key: &str) -> Result<T, Error>;
    fn at<T: Arg>(&self, key: &str) -> Result<T, Error>;
    fn to<T: Arg>(&self) -> Result<T, Error>;
}

impl Body for serde_json::Value {
    fn arg<T: Arg>(&self, index: usize) -> Result<T, Error> {
        let value = self.get("args").ok_or_else(|| Error::new("missing args"))?.get(index).ok_or_else(|| Error::new(&format!("missing arg {}", index)))?;
        T::from_value(value).ok_or_else(|| Error::new(&format!("arg {}: {:?} isn't a {}", index, value, type_name::<T>())))
    }

    fn kwarg<T: Arg>(&self, key: &str) -> Result<T, Error> {
        let value = self.get("kwargs").ok_or_else(|| Error::new("missing kwargs"))?.get(key).ok_or_else(|| Error::new(&format!("missing kwarg {}", key)))?;
        T::from_value(value).ok_or_else(|| Error::new(&format!("kwarg {}: {:?} isn't a {}", key, value, type_name::<T>())))
    }

    fn at<T: Arg>(&self, key: &str) -> Result<T, Error> {
        let value = self.get(key).ok_or_else(|| Error::new(&format!("missing value {}", key)))?;
        T::from_value(value).ok_or_else(|| Error::new(&format!("value {}: {:?} isn't a {}", key, value, type_name::<T>())))
    }

    fn to<T: Arg>(&self) -> Result<T, Error> {
        T::from_value(self).ok_or_else(|| Error::new(&format!("expected a {} but got {:?}", type_name::<T>(), self)))
    }
}

// ===== views ===== //
pub const VIEW_ARGS: [&str; 5] = ["component", "command", "audio", "midi", "evaluate"];

pub type CommandView = extern "C" fn(*const c_void, *const c_char) -> *const c_char;
pub type MidiView = extern "C" fn(*const c_void, *const u8, usize);
pub type AudioView = extern "C" fn(*const c_void) -> *mut f32;
pub type EvaluateView = extern "C" fn(*const c_void);

#[derive(Clone, Debug, PartialEq)]
pub struct View {
    pub raw: *const c_void,
    pub command_view: CommandView,
    pub midi_view: MidiView,
    pub audio_view: AudioView,
    pub evaluate_view: EvaluateView,
}

macro_rules! json_to_ptr {
    ($value:expr, $type:ty) => {{
        let u = match $value.as_str() {
            Some(s) => s.parse::<usize>()?,
            None => return Error::err("pointer isn't a string")?,
        };
        unsafe { transmute::<*const c_void, $type>(u as *const c_void) }
    }};
}

impl View {
    #[allow(clippy::useless_transmute)]
    pub fn new(args: &serde_json::Value) -> Result<Self, Box<dyn StdError>> {
        Ok(Self {
            raw: json_to_ptr!(&args[0], *const c_void),
            command_view: json_to_ptr!(&args[1], CommandView),
            midi_view: json_to_ptr!(&args[2], MidiView),
            audio_view: json_to_ptr!(&args[3], AudioView),
            evaluate_view: json_to_ptr!(&args[4], EvaluateView),
        })
    }

    pub fn command(&self, body: &serde_json::Value) -> Option<serde_json::Value> {
        let text = CString::new(body.to_string()).expect("CString::new failed");
        let result = (self.command_view)(self.raw, text.as_ptr());
        if result.is_null() {
            return None;
        }
        let result = unsafe { CStr::from_ptr(result) }
            .to_str()
            .expect("CStr::to_str failed");
        Some(serde_json::from_str(result).expect("invalid result"))
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

    pub fn name(&self) -> String {
        self.command(&json!({"name": "name"})).unwrap().as_str().unwrap().into()
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
            pub func: Box<FnMut(&mut $specifics, $crate::serde_json::Value) -> Result<Option<$crate::serde_json::Value>, Box<dyn std::error::Error>>>,
            pub info: $crate::serde_json::Value,
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
            let name = unsafe { $crate::CStr::from_ptr(name) }.to_str().expect("CStr::to_str failed").to_string();
            let mut component = Component {
                name: name.clone(),
                specifics: $specifics::new(),
                result: $crate::CString::new("").expect("CString::new failed"),
                commands: CommandMap::new(),
            };
            component.specifics.register_commands(&mut component.commands);
            // name
            component.commands.insert(
                "name",
                Command {
                    func: Box::new(move |_soul, _body| {
                        Ok(Some($crate::json!(name)))
                    }),
                    info: $crate::json!({}),
                },
            );
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
                            let arr: Vec<_> = body.arg(0)?;
                            if arr.len() <= 3 {
                                let mut slice = [0 as u8; 3];
                                for i in 0..arr.len() {
                                    slice[i] = arr[i].to()?;
                                }
                                soul.midi(&slice);
                            } else {
                                let mut vec = Vec::<u8>::new();
                                for i in arr {
                                    vec.push(i.to()?);
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
            let mut list: Vec<$crate::serde_json::Value> = Default::default();
            for (name, command) in &component.commands {
                list.push($crate::json!({
                    "name": name,
                    "info": command.info,
                }));
            }
            list.push($crate::json!({"name": "list", "info": {}}));
            list.sort_by_key(|i| {
                match i["name"].as_str().unwrap() {
                    "name" => "~099",
                    "info" => "~100",
                    "list" => "~101",
                    "join" => "~102",
                    "connect" => "~103",
                    "disconnect" => "~104",
                    "midi" => "~105",
                    "to_json" => "~106",
                    "from_json" => "~107",
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
            let body: $crate::serde_json::Value = match $crate::serde_json::from_str(text) {
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
                let mut audio = audio(component);
                if audio != $crate::null_mut() {
                    use std::time::{SystemTime, UNIX_EPOCH};
                    let timestamp = SystemTime::now()
                        .duration_since(UNIX_EPOCH)
                        .expect("duration_since failed")
                        .as_millis();
                    let percent = percent.parse::<u8>()
                        .expect(&format!("couldn't parse DLAL_SNOOP_AUDIO={} as u8", percent));
                    if (timestamp % 100 < percent as u128) {
                        print!("{:?} audio", component);
                        let samples = std::option_env!("DLAL_SNOOP_AUDIO_SAMPLES").unwrap_or("1").parse::<u32>().unwrap();
                        for i in 0..samples {
                            print!(" {}", unsafe { *audio });
                            unsafe { audio = audio.offset(1) };
                        }
                        println!("");
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
}

#[macro_export]
macro_rules! uni {
    (connect $commands:expr, $check_audio:expr) => {
        command!(
            $commands,
            "connect",
            |soul, body| {
                use $crate::Body;
                let output = $crate::View::new(&body.at("args")?)?;
                if $check_audio && output.audio(0) == None {
                    $crate::Error::err("output must have audio")?;
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
                use $crate::Body;
                let output = View::new(&body.at("args")?)?;
                if soul.output == Some(output) {
                    soul.output = None;
                }
                Ok(None)
            },
            {},
        );
    };
    (audio $self:expr) => {
        match &$self.output {
            Some(output) => output.audio($self.samples_per_evaluation).unwrap(),
            None => return,
        };
    };
}

#[macro_export]
macro_rules! multi {
    (connect $commands:expr, $check_audio:expr) => {
        $crate::command!(
            $commands,
            "connect",
            |soul, body| {
                use $crate::Body;
                let output = $crate::View::new(&body.at("args")?)?;
                if $check_audio && output.audio(0) == None {
                    $crate::Error::err("output must have audio")?;
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
                use $crate::Body;
                let output = $crate::View::new(&body.at("args")?)?;
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
