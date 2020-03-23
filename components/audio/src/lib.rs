use dlal_component_base::{err, gen_component, json, View};

use portaudio as pa;

pub struct Specifics {
    samples_per_evaluation: u32,
    views: Vec<View>,
    stream: Option<pa::Stream<pa::NonBlocking, pa::Duplex<f32, f32>>>,
}

gen_component!(Specifics);

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Specifics {
            samples_per_evaluation: 64,
            views: vec![],
            stream: None,
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        commands.insert(
            "samples_per_evaluation",
            Command {
                func: |soul, body| {
                    soul.samples_per_evaluation = match body["args"][0].as_str() {
                        Some(samples_per_evaluation) => samples_per_evaluation.parse::<u32>()?,
                        None => return Err(err("samples_per_evaluation isn't a string")),
                    };
                    Ok(Some(json!({"result": soul.samples_per_evaluation})))
                },
                info: json!({
                    "args": ["samples_per_evaluation"],
                }),
            },
        );
        commands.insert(
            "add",
            Command {
                func: |soul, body| {
                    let view = View::new(&body["args"])?;
                    println!("{:?}", view.command(json!({"name": "join"})));
                    soul.views.push(view);
                    Ok(None)
                },
                info: json!({
                    "args": ["component", "command", "audio", "midi", "evaluate"],
                }),
            },
        );
        commands.insert(
            "start",
            Command {
                func: |soul, _body| {
                    const SAMPLE_RATE: f64 = 44_100.0;
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
                    pa.is_duplex_format_supported(input_params, output_params, SAMPLE_RATE)?;
                    let views_static = unsafe {
                        std::mem::transmute::<&Vec<View>, &'static Vec<View>>(&soul.views)
                    };
                    let samples_per_evaluation = soul.samples_per_evaluation;
                    soul.stream = Some(pa.open_non_blocking_stream(
                        pa::DuplexStreamSettings::new(
                            input_params,
                            output_params,
                            SAMPLE_RATE,
                            soul.samples_per_evaluation,
                        ),
                        move |args| {
                            assert!(args.frames == samples_per_evaluation as usize);
                            for output_sample in args.out_buffer.iter_mut() {
                                *output_sample = 0.0;
                            }
                            for i in views_static {
                                i.evaluate()
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
                info: json!({}),
            },
        );
        commands.insert(
            "stop",
            Command {
                func: |soul, _body| {
                    match &mut soul.stream {
                        Some(stream) => stream.stop()?,
                        None => (),
                    }
                    Ok(None)
                },
                info: json!({}),
            },
        );
    }

    fn evaluate(&mut self) {}
}
