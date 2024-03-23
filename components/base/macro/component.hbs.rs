pub trait ComponentTrait {
    // fundamentals
    fn init(&mut self) {}
    fn run(&mut self) {}
    fn command(&mut self, body: &dlal_component_base::serde_json::Value) {}
    fn midi(&mut self, _msg: &[u8]) {}
    fn audio(&mut self) -> Option<&mut[f32]> { None }

    // standard command extensions
    fn join(&mut self, body: dlal_component_base::serde_json::Value) -> dlal_component_base::CmdResult { Ok(None) }
    fn connect(&mut self, body: dlal_component_base::serde_json::Value) -> dlal_component_base::CmdResult { Ok(None) }
    fn disconnect(&mut self, body: dlal_component_base::serde_json::Value) -> dlal_component_base::CmdResult { Ok(None) }

    // serialization
    fn to_json_cmd(&mut self, body: dlal_component_base::serde_json::Value) -> dlal_component_base::CmdResult { Ok(None) }
    fn from_json_cmd(&mut self, body: dlal_component_base::serde_json::Value) -> dlal_component_base::CmdResult { Ok(None) }
}

#[derive(Default)]
pub struct Component {
    name: String,
    result: std::ffi::CString,
    {{#if (or features.run_size features.audio)}}
        run_size: usize,
    {{/if}}
    {{#if features.sample_rate}}
        sample_rate: u32,
    {{/if}}
    {{#if features.audio}}
        audio: Vec<f32>,
    {{/if}}
    {{#if features.uni}}
        output: Option<dlal_component_base::View>,
    {{/if}}
    {{#if features.multi}}
        outputs: Vec<dlal_component_base::View>,
    {{/if}}
    {{fields}}
}

impl Component {
    fn set_result(&mut self, result: &str) -> *const std::os::raw::c_char {
        self.result = std::ffi::CString::new(result).expect("CString::new failed");
        self.result.as_ptr()
    }

    fn join_cmd(&mut self, body: dlal_component_base::serde_json::Value) -> dlal_component_base::CmdResult {
        use dlal_component_base::Body;
        {{#if (or features.run_size features.audio)}}
            self.run_size = body.kwarg("run_size")?;
        {{/if}}
        {{#if features.sample_rate}}
            self.sample_rate = body.kwarg("sample_rate")?;
        {{/if}}
        {{#if features.audio}}
            self.audio.resize(self.run_size, 0.0);
        {{/if}}
        self.join(body)
    }

    fn connect_cmd(&mut self, body: dlal_component_base::serde_json::Value) -> dlal_component_base::CmdResult {
        {{#if (or features.uni features.multi)}}
            use dlal_component_base::Body;
            let output = dlal_component_base::View::new(&body.at("args")?)?;
            {{#if features.check_audio}}
                if output.audio(0) == None {
                    Err(dlal_component_base::err!("output must have audio"))?;
                }
            {{/if}}
            {{#if features.uni}}
                self.output = Some(output);
            {{else}}
                self.outputs.push(output);
            {{/if}}
        {{/if}}
        self.connect(body)
    }

    fn disconnect_cmd(&mut self, body: dlal_component_base::serde_json::Value) -> dlal_component_base::CmdResult {
        {{#if (or features.uni features.multi)}}
            use dlal_component_base::Body;
            let output = dlal_component_base::View::new(&body.at("args")?)?;
            {{#if features.uni}}
                if self.output == Some(output) {
                    self.output = None;
                }
            {{else}}
                if let Some(i) = self.outputs.iter().position(|i| i == &output) {
                    self.outputs.remove(i);
                }
            {{/if}}
        {{/if}}
        self.disconnect(body)
    }

    fn midi_cmd(&mut self, body: dlal_component_base::serde_json::Value) -> dlal_component_base::CmdResult {
        use dlal_component_base::Body;
        let arr: Vec<u8> = body.arg(0)?;
        if arr.len() <= 3 {
            let mut slice = [0 as u8; 3];
            for i in 0..arr.len() {
                slice[i] = arr[i];
            }
            self.midi(&slice);
        } else {
            let mut vec = Vec::<u8>::new();
            for i in arr {
                vec.push(i);
            }
            self.midi(vec.as_slice());
        }
        Ok(None)
    }

    {{#if features.uni}}
        fn uni_midi(&self, msg: &[u8]) {
            if let Some(output) = self.output.as_ref() {
                output.midi(msg);
            };
        }

        fn uni_audio(&self, audio: &[f32]) {
            if let Some(output) = self.output.as_ref() {
                let audio_o = output.audio(audio.len()).unwrap();
                for i in 0..audio.len() {
                    audio_o[i] += audio[i];
                }
            };
        }
    {{/if}}

    {{#if features.multi}}
        fn multi_midi(&self, msg: &[u8]) {
            for output in &self.outputs {
                output.midi(msg);
            }
        }

        fn multi_audio(&self, audio: &[f32]) {
            for output in &self.outputs {
                let audio_o = output.audio(audio.len()).unwrap();
                for i in 0..audio.len() {
                    audio_o[i] += audio[i];
                }
            }
        }
    {{/if}}

    {{#if features.audio}}
        fn audio(&mut self) -> Option<&mut[f32]> {
            Some(self.audio.as_mut_slice())
        }
    {{/if}}

    {{#if features.field_helpers.json}}
        fn to_json_cmd(&mut self, _body: dlal_component_base::serde_json::Value) -> dlal_component_base::CmdResult {
            Ok(Some(dlal_component_base::json!({
                {{#each features.field_helpers.json}}
                    "{{this}}": self.{{this}},
                {{/each}}
            })))
        }

        fn from_json_cmd(&mut self, body: dlal_component_base::serde_json::Value) -> dlal_component_base::CmdResult {
            use dlal_component_base::Body;
            let j: dlal_component_base::serde_json::Value = body.arg(0)?;
            {{#each features.field_helpers.json}}
                self.{{this}} = j.at("{{this}}")?;
            {{/each}}
            Ok(None)
        }
    {{/if}}

    {{#each features.field_helpers.rw}}
        fn {{this}}_cmd(&mut self, body: dlal_component_base::serde_json::Value) -> dlal_component_base::CmdResult {
            use dlal_component_base::Body;
            match body.arg(0) {
                Ok(v) => self.{{this}} = v,
                e => if body.has_arg(0) {
                    e?;
                }
            }
            Ok(Some(dlal_component_base::serde_json::json!(self.{{this}})))
        }
    {{/each}}

    {{#each features.field_helpers.r}}
        fn {{this}}_cmd(&mut self, body: dlal_component_base::serde_json::Value) -> dlal_component_base::CmdResult {
            use dlal_component_base::Body;
            Ok(Some(dlal_component_base::serde_json::json!(self.{{this}})))
        }
    {{/each}}
}

impl std::fmt::Debug for Component {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Component")
            .field("name", &self.name)
            .finish()
    }
}

impl std::fmt::Display for Component {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.name)
    }
}

#[no_mangle]
pub unsafe extern "C" fn construct(name: *const std::os::raw::c_char) -> *mut Component {
    let name = unsafe { std::ffi::CStr::from_ptr(name) }.to_str().expect("CStr::to_str failed").to_string();
    let mut component = Component {
        name: name.clone(),
        result: std::ffi::CString::new("").expect("CString::new failed"),
        ..Default::default()
    };
    component.init();
    {{#if features.multi}}
        component.outputs.reserve(1);
    {{/if}}
    Box::into_raw(Box::new(component))
}

#[no_mangle]
pub unsafe extern "C" fn destruct(component: *mut Component) {
    drop(unsafe { Box::from_raw(component) });
}

#[no_mangle]
pub unsafe extern "C" fn command(component: *mut Component, text: *const std::os::raw::c_char) -> *const std::os::raw::c_char {
    let component = unsafe { &mut *component };
    let text = unsafe { std::ffi::CStr::from_ptr(text) }.to_str().expect("CStr::to_str failed");
    if std::option_env!("DLAL_SNOOP_COMMAND").is_some() {
        println!("{} command {:02x?}", component, text);
    }
    let body: dlal_component_base::serde_json::Value = match dlal_component_base::serde_json::from_str(text) {
        Ok(body) => body,
        Err(err) => return component.set_result(&dlal_component_base::json!({"error": err.to_string()}).to_string()),
    };
    component.command(&body);
    let name = match body["name"].as_str() {
        Some(name) => name,
        None => return component.set_result(&dlal_component_base::json!({"error": "command name isn't a string"}).to_string()),
    };
    let result: dlal_component_base::CmdResult = match name {
        {{#each commands}}
            "{{this.name}}" => component.{{this.name}}_cmd(body),
        {{/each}}
        "name" => Ok(Some(dlal_component_base::json!(component.name))),
        "info" => Ok(Some(dlal_component_base::json!({{info}}))),
        "list" => Ok(Some(dlal_component_base::json!([
            {{#each commands}}
                {
                    "name": "{{this.name}}",
                    "info": {{this.info}},
                },
            {{/each}}
            {
                "name": "name",
                "info": {},
            },
            {
                "name": "info",
                "info": {},
            },
            {
                "name": "list",
                "info": {},
            },
            {
                "name": "join",
                "info":
                    {{#if features.join_info}}
                        {{features.join_info}}
                    {{else}}
                        {
                            "kwargs": [
                                {{#if (or features.run_size features.audio)}}
                                    "run_size",
                                {{/if}}
                                {{#if features.sample_rate}}
                                    "sample_rate",
                                {{/if}}
                            ],
                        },
                    {{/if}}
            },
            {
                "name": "connect",
                "info":
                    {{#if features.connect_info}}
                        {{features.connect_info}}
                    {{else}}
                        {
                            "args": "view",
                            {{#if features.uni}}
                                "flavor": "uni",
                            {{/if}}
                            {{#if features.multi}}
                                "flavor": "multi",
                            {{/if}}
                        },
                    {{/if}}
            },
            {
                "name": "disconnect",
                "info":
                    {{#if features.disconnect_info}}
                        {{features.disconnect_info}}
                    {{else}}
                        {
                            {{#if features.uni}}
                                "flavor": "uni",
                            {{/if}}
                            {{#if features.multi}}
                                "args": "view",
                                "flavor": "multi",
                            {{/if}}
                        },
                    {{/if}}
            },
            {
                "name": "midi",
                "info": { "args": ["msg"] },
            },
            {
                "name": "to_json",
                "info": {},
            },
            {
                "name": "from_json",
                "info": { "args": ["json"] },
            },
        ]))),
        "join" => component.join_cmd(body),
        "connect" => component.connect_cmd(body),
        "disconnect" => component.disconnect_cmd(body),
        "midi" => component.midi_cmd(body),
        "to_json" => component.to_json_cmd(body),
        "from_json" => component.from_json_cmd(body),
        _ => return component.set_result(&dlal_component_base::json!({"error": format!(r#"no such command "{}""#, name)}).to_string()),
    };
    match result {
        Ok(success) => match(success) {
            Some(v) => component.set_result(&v.to_string()),
            None => std::ptr::null(),
        },
        Err(err) => component.set_result(&dlal_component_base::json!({"error": err.to_string()}).to_string()),
    }
}

#[no_mangle]
pub unsafe extern "C" fn midi(component: *mut Component, msg: *const u8, size: usize) {
    let component = unsafe { &mut *component };
    let msg = unsafe { std::slice::from_raw_parts(msg, size) };
    if std::option_env!("DLAL_SNOOP_MIDI").is_some() {
        println!("{} midi {:02x?}", component, msg);
    }
    component.midi(msg);
}

#[no_mangle]
pub unsafe extern "C" fn audio(component: *mut Component) -> *mut f32 {
    let component = unsafe { &mut *component };
    match component.audio() {
        Some(audio) => audio.as_mut_ptr(),
        None => std::ptr::null_mut(),
    }
}

#[no_mangle]
pub unsafe extern "C" fn run(component: *mut Component) {
    let component = unsafe { &mut *component };
    if let Some(percent) = std::option_env!("DLAL_SNOOP_AUDIO") {
        let mut audio = audio(component);
        if !audio.is_null() {
            let timestamp = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .expect("duration_since failed")
                .as_millis();
            let percent = percent.parse::<u8>()
                .expect(&format!("couldn't parse DLAL_SNOOP_AUDIO={} as u8", percent));
            if (timestamp % 100 < percent as u128) {
                print!("{} audio", component);
                let samples = std::option_env!("DLAL_SNOOP_AUDIO_SAMPLES").unwrap_or("1").parse::<u32>().unwrap();
                for i in 0..samples {
                    print!(" {:.2e}", unsafe { *audio });
                    unsafe { audio = audio.offset(1) };
                }
                println!("");
            }
        }
    }
    component.run();
}

#[allow(unused_macros)]
macro_rules! field_helper_to_json {
    ($self:expr, $extra:tt) => {
        dlal_component_base::serde_json::json!({
            {{#each features.field_helpers.all}}
                "{{this}}": $self.{{this}},
            {{/each}}
            "_extra": $extra
        })
    }
}

#[allow(unused_macros)]
macro_rules! field_helper_from_json {
    ($self:expr, $body:expr) => {
        {
            use dlal_component_base::Body;
            let j = $body.arg::<dlal_component_base::serde_json::Value>(0)?;
            {{#each features.field_helpers.all}}
                $self.{{this}} = j.at("{{this}}")?;
            {{/each}}
            j
        }
    }
}
