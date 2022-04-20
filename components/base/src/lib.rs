pub use dlal_component_macro::component;

pub use serde_json;
pub use serde_json::json;

use std::any::type_name;
use std::error::Error as StdError;
pub use std::ffi::{CStr, CString};
use std::fmt;
pub use std::mem::transmute;
pub use std::os::raw::{c_char, c_void};
use std::slice::from_raw_parts_mut;

// ===== CmdResult ===== //
pub type CmdResult = Result<Option<serde_json::Value>, Box<dyn StdError>>;

// ===== Error ===== //
#[derive(Debug)]
pub struct Error {
    msg: String,
}

impl Error {
    pub fn new(msg: &str) -> Self {
        Self { msg: msg.into() }
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

#[macro_export]
macro_rules! err {
    ($($arg:tt)+) => {
        $crate::Error::new(&format!($($arg)+))
    };
}

// ===== arg handling ===== //
// ----- Arg ------ //
pub trait Arg {
    fn from_value(value: &serde_json::Value) -> Option<Self>
    where
        Self: Sized;

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

impl<T: Arg> Arg for Vec<T> {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        match value.as_array() {
            Some(v) => v.clone().vec().ok(),
            None => None,
        }
    }
}

impl Arg for serde_json::Map<String, serde_json::Value> {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        value.as_object().cloned()
    }
}

impl Arg for serde_json::Value {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        Some(value.clone())
    }
}

// ----- Body ----- //
pub trait Body {
    fn has_arg(&self, index: usize) -> bool;
    fn arg<T: Arg>(&self, index: usize) -> Result<T, Error>;
    fn has_kwarg(&self, key: &str) -> bool;
    fn kwarg<T: Arg>(&self, key: &str) -> Result<T, Error>;
    fn at<T: Arg>(&self, key: &str) -> Result<T, Error>;
    fn to<T: Arg>(&self) -> Result<T, Error>;
}

impl Body for serde_json::Value {
    fn has_arg(&self, index: usize) -> bool {
        let args = match self.get("args") {
            Some(args) => args,
            _ => return false,
        };
        args.get(index).is_some()
    }

    fn arg<T: Arg>(&self, index: usize) -> Result<T, Error> {
        let value = self
            .get("args")
            .ok_or_else(|| err!("missing args"))?
            .get(index)
            .ok_or_else(|| err!("missing arg {}", index))?;
        T::from_value(value)
            .ok_or_else(|| err!("arg {}: {:?} isn't a {}", index, value, type_name::<T>()))
    }

    fn has_kwarg(&self, key: &str) -> bool {
        let kwargs = match self.get("kwargs") {
            Some(kwargs) => kwargs,
            _ => return false,
        };
        kwargs.get(key).is_some()
    }

    fn kwarg<T: Arg>(&self, key: &str) -> Result<T, Error> {
        let value = self
            .get("kwargs")
            .ok_or_else(|| err!("missing kwargs"))?
            .get(key)
            .ok_or_else(|| err!("missing kwarg {}", key))?;
        T::from_value(value)
            .ok_or_else(|| err!("kwarg {}: {:?} isn't a {}", key, value, type_name::<T>()))
    }

    fn at<T: Arg>(&self, key: &str) -> Result<T, Error> {
        let value = self.get(key).ok_or_else(|| err!("missing value {}", key))?;
        T::from_value(value)
            .ok_or_else(|| err!("value {}: {:?} isn't a {}", key, value, type_name::<T>()))
    }

    fn to<T: Arg>(&self) -> Result<T, Error> {
        T::from_value(self)
            .ok_or_else(|| err!("expected a {} but got {:?}", type_name::<T>(), self))
    }
}

// ===== View ===== //
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
    pub run_view: EvaluateView,
}

#[macro_export]
macro_rules! json_to_ptr {
    ($value:expr, $type:ty) => {{
        let u = match $value.as_str() {
            Some(s) => s.parse::<usize>()?,
            None => return Err($crate::err!("pointer isn't a string").into()),
        };
        #[allow(clippy::useless_transmute)]
        unsafe {
            $crate::transmute::<*const $crate::c_void, $type>(u as *const $crate::c_void)
        }
    }};
}

impl View {
    pub fn new(args: &serde_json::Value) -> Result<Self, Box<dyn StdError>> {
        Ok(Self {
            raw: json_to_ptr!(&args[0], *const c_void),
            command_view: json_to_ptr!(&args[1], CommandView),
            midi_view: json_to_ptr!(&args[2], MidiView),
            audio_view: json_to_ptr!(&args[3], AudioView),
            run_view: json_to_ptr!(&args[4], EvaluateView),
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

    pub fn audio(&self, run_size: usize) -> Option<&mut [f32]> {
        let audio = (self.audio_view)(self.raw);
        if audio.is_null() {
            None
        } else {
            Some(unsafe { from_raw_parts_mut(audio, run_size) })
        }
    }

    pub fn run(&self) {
        (self.run_view)(self.raw);
    }

    pub fn name(&self) -> String {
        self.command(&json!({"name": "name"}))
            .unwrap()
            .as_str()
            .unwrap()
            .into()
    }
}
