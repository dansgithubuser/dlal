use dlal_component_base::{component, err, json, serde_json, Body, CmdResult, View};

use colored::*;
use portaudio as pa;

use std::ptr::{null, null_mut};
use std::slice::{from_raw_parts, from_raw_parts_mut};

struct Audio {
    i: *const f32,
    o: *mut f32,
}

impl Default for Audio {
    fn default() -> Self {
        Self {
            i: null(),
            o: null_mut(),
        }
    }
}

enum Stream {
    None,
    Duplex(pa::Stream<pa::NonBlocking, pa::Duplex<f32, f32>>),
    Input(pa::Stream<pa::NonBlocking, pa::Input<f32>>),
}

impl Default for Stream {
    fn default() -> Self { Stream::None }
}

component!(
    {"in": ["audio**"], "out": ["audio**"]},
    [
        "multi",
        "check_audio",
        "run_size",
        "sample_rate",
        {"name": "field_helpers", "fields": ["run_size", "sample_rate"], "kinds": ["rw", "json"]},
    ],
    {
        addees: Vec<Vec<View>>,
        stream: Stream,
        audio: Audio,
    },
    {
        "add": {"args": ["component", "command", "audio", "midi", "run"]},
        "remove": {"args": ["component", "command", "audio", "midi", "run"]},
        "start": {},
        "start_input_only": {},
        "stop": {},
        "run": {},
        "run_explain": {},
        "addee_order": {},
        "version": {},
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.run_size = 64;
        self.sample_rate = 44100;
    }

    fn run(&mut self) {
        let audio_i = unsafe { from_raw_parts(self.audio.i, self.run_size) };
        self.multi_audio(audio_i);
    }

    fn audio(&mut self) -> Option<&mut [f32]> {
        if self.audio.o.is_null() {
            return Some(&mut []);
        }
        Some(unsafe { from_raw_parts_mut(self.audio.o, self.run_size) })
    }
}

impl Component {
    fn run_addees(&mut self) {
        for slot in self.addees.iter().rev() {
            for i in slot {
                i.run();
            }
        }
    }

    fn run_addees_explain(&mut self) {
        for slot in self.addees.iter().rev() {
            for i in slot {
                self.explain();
                println!("{} {}", "run".green().bold(), i.name().green(),);
                i.run();
            }
        }
    }

    fn explain(&self) {
        for slot in self.addees.iter().rev() {
            for i in slot {
                if let Some(audio) = i.audio(self.run_size) {
                    println!(
                        "{} {} {:?}",
                        "audio".yellow().bold(),
                        i.name().yellow(),
                        audio,
                    );
                }
            }
        }
    }

    fn add_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let view = View::new(&body.at("args")?)?;
        let slot: usize = body.arg(5)?;
        let join_result = view.command(&json!({
            "name": "join",
            "kwargs": {
                "run_size": self.run_size,
                "sample_rate": self.sample_rate,
            },
        }));
        if let Some(join_result) = join_result {
            if let Some(obj) = join_result.as_object() {
                if obj.get("error").is_some() {
                    return Ok(Some(join_result));
                }
            }
        }
        if slot >= self.addees.len() {
            self.addees.resize(slot + 1, vec![]);
        }
        self.addees[slot].push(view);
        Ok(None)
    }

    fn remove_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let view = View::new(&body.at("args")?)?;
        for slot in 0..self.addees.len() {
            if let Some(index) = self.addees[slot].iter().position(|i| i.raw == view.raw) {
                self.addees[slot].remove(index);
                break;
            }
            if slot == self.addees.len() - 1 {
                return Err(err!("no such component").into());
            }
        }
        Ok(None)
    }

    fn start_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        const CHANNELS: i32 = 1;
        const INTERLEAVED: bool = true;
        let pa = pa::PortAudio::new()?;
        let input_device = pa.default_input_device()?;
        let input_params = pa::StreamParameters::<f32>::new(
            input_device,
            CHANNELS,
            INTERLEAVED,
            pa.device_info(input_device)?.default_low_input_latency,
        );
        let output_device = pa.default_output_device()?;
        let output_params = pa::StreamParameters::<f32>::new(
            output_device,
            CHANNELS,
            INTERLEAVED,
            pa.device_info(output_device)?.default_low_output_latency,
        );
        pa.is_duplex_format_supported(input_params, output_params, self.sample_rate.into())?;
        let self_scoped = unsafe { std::mem::transmute::<&mut Component, &mut Component>(self) };
        self.stream = Stream::Duplex({
            let mut stream = pa.open_non_blocking_stream(
                pa::DuplexStreamSettings::new(
                    input_params,
                    output_params,
                    self.sample_rate.into(),
                    self.run_size as u32,
                ),
                move |args| {
                    assert!(args.frames == self_scoped.run_size);
                    for output_sample in args.out_buffer.iter_mut() {
                        *output_sample = 0.0;
                    }
                    self_scoped.audio.i = args.in_buffer.as_ptr();
                    self_scoped.audio.o = args.out_buffer.as_mut_ptr();
                    self_scoped.run_addees();
                    pa::Continue
                },
            )?;
            stream.start()?;
            stream
        });
        Ok(None)
    }

    fn start_input_only_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        const CHANNELS: i32 = 1;
        const INTERLEAVED: bool = true;
        let pa = pa::PortAudio::new()?;
        let input_device = pa.default_input_device()?;
        let input_params = pa::StreamParameters::<f32>::new(
            input_device,
            CHANNELS,
            INTERLEAVED,
            pa.device_info(input_device)?.default_low_input_latency,
        );
        let self_scoped = unsafe { std::mem::transmute::<&mut Component, &mut Component>(self) };
        self.stream = Stream::Input({
            let mut stream = pa.open_non_blocking_stream(
                pa::InputStreamSettings::new(
                    input_params,
                    self.sample_rate.into(),
                    self.run_size as u32,
                ),
                move |args| {
                    assert!(args.frames == self_scoped.run_size);
                    self_scoped.audio.i = args.buffer.as_ptr();
                    self_scoped.run_addees();
                    pa::Continue
                },
            )?;
            stream.start()?;
            stream
        });
        Ok(None)
    }

    fn stop_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        match &mut self.stream {
            Stream::Duplex(stream) => stream.stop()?,
            Stream::Input(stream) => stream.stop()?,
            Stream::None => (),
        }
        Ok(None)
    }

    fn run_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        let mut vec: Vec<f32> = Vec::new();
        vec.resize(self.run_size, 0.0);
        self.audio.o = vec.as_mut_ptr();
        for j in &mut vec {
            *j = 0.0;
        }
        self.run_addees();
        Ok(None)
    }

    fn run_explain_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        let mut vec: Vec<f32> = Vec::new();
        vec.resize(self.run_size, 0.0);
        self.audio.o = vec.as_mut_ptr();
        for j in &mut vec {
            *j = 0.0;
        }
        self.run_addees_explain();
        Ok(None)
    }

    fn addee_order_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        let mut result = Vec::<String>::new();
        for slot in self.addees.iter().rev() {
            for i in slot {
                result.push(i.name());
            }
        }
        Ok(Some(json!(result)))
    }

    fn version_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!(pa::version_text()?)))
    }
}
