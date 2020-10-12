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

component!(
    {"in": ["audio**"], "out": ["audio**"]},
    ["multi", "check_audio", "samples_per_evaluation", "sample_rate"],
    {
        addees: Vec<Vec<View>>,
        stream: Option<pa::Stream<pa::NonBlocking, pa::Duplex<f32, f32>>>,
        audio: Audio,
    },
    {
        "samples_per_evaluation": {"args": [{"name": "samples_per_evaluation", "optional": true}]},
        "sample_rate": {"args": [{"name": "sample_rate", "optional": true}]},
        "add": {"args": ["component", "command", "audio", "midi", "evaluate"]},
        "remove": {"args": ["component", "command", "audio", "midi", "evaluate"]},
        "start": {},
        "stop": {},
        "run": {},
        "run_explain": {},
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.samples_per_evaluation = 64;
        self.sample_rate = 44100;
    }

    fn evaluate(&mut self) {
        let audio_i = unsafe { from_raw_parts(self.audio.i, self.samples_per_evaluation) };
        self.multi_audio(audio_i);
    }

    fn audio(&mut self) -> Option<&mut [f32]> {
        if self.audio.o.is_null() {
            return Some(&mut []);
        }
        Some(unsafe { from_raw_parts_mut(self.audio.o, self.samples_per_evaluation) })
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({
            "samples_per_evaluation": self.samples_per_evaluation.to_string(),
            "sample_rate": self.sample_rate.to_string(),
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.samples_per_evaluation = body.kwarg("samples_per_evaluation")?;
        self.sample_rate = body.kwarg("sample_rate")?;
        Ok(None)
    }
}

impl Component {
    fn evaluate_addees(&mut self) {
        for slot in self.addees.iter().rev() {
            for i in slot {
                i.evaluate();
            }
        }
    }

    fn evaluate_addees_explain(&mut self) {
        for slot in self.addees.iter().rev() {
            for i in slot {
                self.explain();
                println!("{} {}", "evaluate".green().bold(), i.name().green(),);
                i.evaluate();
            }
        }
    }

    fn explain(&self) {
        for slot in self.addees.iter().rev() {
            for i in slot {
                if let Some(audio) = i.audio(self.samples_per_evaluation) {
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

    fn samples_per_evaluation_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.samples_per_evaluation = v;
        }
        Ok(Some(json!(self.samples_per_evaluation)))
    }

    fn sample_rate_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.sample_rate = v;
        }
        Ok(Some(json!(self.sample_rate)))
    }

    fn add_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let view = View::new(&body.at("args")?)?;
        let slot: usize = body.arg(5)?;
        let join_result = view.command(&json!({
            "name": "join",
            "kwargs": {
                "samples_per_evaluation": self.samples_per_evaluation,
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
            pa.device_info(input_device)?.default_high_input_latency,
        );
        let output_device = pa.default_output_device()?;
        let output_params = pa::StreamParameters::<f32>::new(
            output_device,
            CHANNELS,
            INTERLEAVED,
            pa.device_info(output_device)?.default_high_output_latency,
        );
        pa.is_duplex_format_supported(input_params, output_params, self.sample_rate.into())?;
        let self_scoped = unsafe { std::mem::transmute::<&mut Component, &mut Component>(self) };
        self.stream = Some(pa.open_non_blocking_stream(
            pa::DuplexStreamSettings::new(
                input_params,
                output_params,
                self.sample_rate.into(),
                self.samples_per_evaluation as u32,
            ),
            move |args| {
                assert!(args.frames == self_scoped.samples_per_evaluation);
                for output_sample in args.out_buffer.iter_mut() {
                    *output_sample = 0.0;
                }
                self_scoped.audio.i = args.in_buffer.as_ptr();
                self_scoped.audio.o = args.out_buffer.as_mut_ptr();
                self_scoped.evaluate_addees();
                pa::Continue
            },
        )?);
        match &mut self.stream {
            Some(stream) => stream.start()?,
            None => (),
        }
        Ok(None)
    }

    fn stop_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        match &mut self.stream {
            Some(stream) => stream.stop()?,
            None => (),
        }
        Ok(None)
    }

    fn run_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        let mut vec: Vec<f32> = Vec::new();
        vec.resize(self.samples_per_evaluation, 0.0);
        self.audio.o = vec.as_mut_ptr();
        for j in &mut vec {
            *j = 0.0;
        }
        self.evaluate_addees();
        Ok(None)
    }

    fn run_explain_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        let mut vec: Vec<f32> = Vec::new();
        vec.resize(self.samples_per_evaluation, 0.0);
        self.audio.o = vec.as_mut_ptr();
        for j in &mut vec {
            *j = 0.0;
        }
        self.evaluate_addees_explain();
        Ok(None)
    }
}
