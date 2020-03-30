use dlal_component_base::{arg_num, args, command, gen_component, json, View};

use portaudio as pa;

use std::ptr::null_mut;
use std::slice::from_raw_parts_mut;

const SAMPLE_RATE: f64 = 44100.0;

pub struct Specifics {
    samples_per_evaluation: usize,
    views: Vec<View>,
    stream: Option<pa::Stream<pa::NonBlocking, pa::Duplex<f32, f32>>>,
    audio: *mut f32,
}

gen_component!(Specifics);

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Specifics {
            samples_per_evaluation: 64,
            views: vec![],
            stream: None,
            audio: null_mut(),
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        command!(
            commands,
            "samples_per_evaluation",
            |soul, body| {
                if let Ok(v) = arg_num(&body, 0) {
                    soul.samples_per_evaluation = v;
                }
                Ok(Some(json!(soul.samples_per_evaluation.to_string())))
            },
            { "args": [{"name": "samples_per_evaluation", "optional": true}] },
        );
        command!(
            commands,
            "add",
            |soul, body| {
                let view = View::new(args(&body)?)?;
                let join_result = view.command(json!({
                    "name": "join",
                    "kwargs": {
                        "samples_per_evaluation": soul.samples_per_evaluation.to_string(),
                        "sample_rate": SAMPLE_RATE.to_string(),
                    },
                }));
                if let Some(join_result) = join_result {
                    if let Some(obj) = join_result.as_object() {
                        if obj.get("error").is_some() {
                            return Ok(Some(join_result));
                        }
                    }
                }
                soul.views.push(view);
                Ok(None)
            },
            { "args": ["component", "command", "audio", "midi", "evaluate"] },
        );
        command!(
            commands,
            "start",
            |mut soul, _body| {
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
                pa.is_duplex_format_supported(input_params, output_params, SAMPLE_RATE)?;
                let soul_scoped =
                    unsafe { std::mem::transmute::<&mut Specifics, &mut Specifics>(&mut soul) };
                soul.stream = Some(pa.open_non_blocking_stream(
                    pa::DuplexStreamSettings::new(
                        input_params,
                        output_params,
                        SAMPLE_RATE,
                        soul.samples_per_evaluation as u32,
                    ),
                    move |args| {
                        assert!(args.frames == soul_scoped.samples_per_evaluation);
                        for output_sample in args.out_buffer.iter_mut() {
                            *output_sample = 0.0;
                        }
                        soul_scoped.audio = args.out_buffer.as_mut_ptr();
                        for i in &mut soul_scoped.views {
                            i.evaluate();
                        }
                        pa::Continue
                    },
                )?);
                match &mut soul.stream {
                    Some(stream) => stream.start()?,
                    None => (),
                }
                Ok(None)
            },
            {},
        );
        command!(
            commands,
            "stop",
            |soul, _body| {
                match &mut soul.stream {
                    Some(stream) => stream.stop()?,
                    None => (),
                }
                Ok(None)
            },
            {},
        );
        command!(
            commands,
            "to_json",
            |soul, _body| { Ok(Some(json!(soul.samples_per_evaluation.to_string()))) },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                soul.samples_per_evaluation = arg_num(&body, 0)?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {}

    fn audio(&mut self) -> Option<&mut [f32]> {
        if self.audio.is_null() {
            return Some(&mut []);
        }
        Some(unsafe { from_raw_parts_mut(self.audio, self.samples_per_evaluation) })
    }
}
