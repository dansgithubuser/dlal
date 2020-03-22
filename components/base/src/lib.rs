pub use serde_json::from_str as json_from_str;
pub use serde_json::json;
pub use serde_json::Value as JsonValue;

#[macro_export]
macro_rules! gen_component {
    ($specifics:ident) => {
        pub struct Command {
            pub func: fn(&mut $specifics, dlal_base::JsonValue) -> Option<dlal_base::JsonValue>,
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
                Err(err) => return component.set_result(&format!(r#"{{"error": "{}"}}"#, err)),
            };
            let name = match body["name"].as_str() {
                Some(name) => name,
                None => return component.set_result(r#"{"error": "command name isn't a string"}"#),
            };
            match (component.commands[name].func)(&mut component.specifics, body) {
                Some(result) => component.set_result(&result.to_string()),
                None => std::ptr::null(),
            }
        }

        #[no_mangle]
        pub extern "C" fn evaluate(component: *mut Component) {
            let component = unsafe { &mut *component };
            component.specifics.evaluate();
        }
    }
}
