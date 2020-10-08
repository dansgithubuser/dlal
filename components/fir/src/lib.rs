use dlal_component_base::{command, gen_component, join, json, uni, View, Body, serde_json, Arg};

use rustfft::{num_complex::Complex, FFTplanner};

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    ir: Vec<f32>,
    state: Vec<f32>,
    index: usize,
    output: Option<View>,
}

impl Specifics {
    fn set_ir(&mut self, ir: Vec<f32>) {
        self.ir = ir;
        self.state.resize(self.ir.len(), 0.0);
        if self.index > self.state.len() {
            self.index = 0;
        }
    }
}

gen_component!(Specifics, {"in": [], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            ..Default::default()
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                soul.samples_per_evaluation = body.kwarg("samples_per_evaluation")?;
                Ok(None)
            },
            ["samples_per_evaluation"],
        );
        uni!(connect commands, true);
        command!(
            commands,
            "ir",
            |soul, body| {
                soul.set_ir(body.arg::<Vec<_>>(0)?.vec()?);
                Ok(None)
            },
            { "args": ["ir"] },
        );
        command!(
            commands,
            "bandpass",
            |soul, body| {
                let center: f32 = body.arg(0)?;
                let width: f32 = match body.arg(1) {
                    Ok(width) => width,
                    Err(_) => 2.0,
                };
                let size: usize = match body.arg(2) {
                    Ok(size) => size,
                    Err(_) => 128,
                };
                let amplitude: f32 = match body.arg(3) {
                    Ok(amplitude) => amplitude,
                    Err(_) => 1.0,
                };
                let mut fr = (0..(size + 1)).map(|i| {
                    Complex::new(
                        amplitude * (1.0 - ((i as f32 - center * size as f32) / width).powf(2.0)).max(0.0),
                        0.0,
                    )
                }).collect::<Vec<Complex<f32>>>();
                for i in 1..size {
                    fr.push(fr[size - i]);
                }
                let mut planner = FFTplanner::new(true);
                let fft = planner.plan_fft(2 * size);
                let mut ir = vec![Complex::<f32>::new(0.0, 0.0); 2 * size];
                fft.process(&mut fr, &mut ir);
                soul.set_ir(ir.iter().map(|i| i.re).collect());
                Ok(None)
            },
            {
                "args": [
                    {
                        "name": "center",
                        "range": "[0, 1]",
                    },
                    {
                        "name": "width",
                        "optional": true,
                        "default": 2.0,
                    },
                    {
                        "name": "size",
                        "optional": true,
                        "default": "128",
                    },
                    {
                        "name": "amplitude",
                        "optional": true,
                        "default": "1",
                    },
                ],
            },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| {
                Ok(Some(json!({
                    "ir": soul.ir,
                })))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                let j = body.arg::<serde_json::Value>(0)?;
                soul.set_ir(j.at::<Vec<_>>("ir")?.vec()?);
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        if self.ir.is_empty() {
            return;
        }
        if let Some(output) = &self.output {
            for i in output.audio(self.samples_per_evaluation).unwrap() {
                self.state[self.index] = *i;
                *i = 0.0;
                for j in 0..self.ir.len() {
                    *i += self.ir[j] * self.state[(self.index + j) % self.state.len()];
                }
                self.index += self.state.len() - 1;
                self.index %= self.state.len();
            }
        }
    }
}
