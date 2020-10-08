use dlal_component_base::{command, gen_component, join, json, uni, View, Body};

use std::f32::consts::PI;

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    sample_rate: u32,
    a: f32,
    x: f32,
    y: f32,
    output: Option<View>,
}

gen_component!(Specifics, {"in": [], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            a: 0.05,
            ..Default::default()
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                soul.samples_per_evaluation = body.kwarg("samples_per_evaluation")?;
                soul.sample_rate = body.kwarg("sample_rate")?;
                Ok(None)
            },
            ["samples_per_evaluation", "sample_rate"],
        );
        uni!(connect commands, true);
        command!(
            commands,
            "set",
            |soul, body| {
                if let Ok(highness) = body.arg::<f32>(0) {
                    soul.a = 1.0 - highness;
                }
                Ok(Some(json!(1.0 - soul.a)))
            },
            {
                "args": [{
                    "name": "highness",
                    "optional": true,
                    "range": "[0, 1]",
                }],
            }
        );
        command!(
            commands,
            "freq",
            |soul, body| {
                if let Ok(sample_rate) = body.arg(1) {
                    soul.sample_rate = sample_rate;
                }
                if let Ok(freq) = body.arg::<f32>(0) {
                    soul.a = 1.0 / (2.0 * PI / soul.sample_rate as f32 * freq + 1.0);
                }
                Ok(Some(json!((1.0 / soul.a - 1.0) / (2.0 * PI / soul.sample_rate as f32))))
            },
            {
                "args": [
                    {
                        "name": "freq",
                        "optional": true,
                    },
                    {
                        "name": "sample_rate",
                        "optional": true,
                    },
                ],
            }
        );
        command!(
            commands,
            "to_json",
            |soul, _body| { Ok(Some(json!(soul.a))) },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                soul.a = body.arg(0)?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        if let Some(output) = &self.output {
            let audio = output.audio(self.samples_per_evaluation).unwrap();
            for i in 0..self.samples_per_evaluation {
                let x = audio[i];
                audio[i] = self.a * (self.y + x - self.x);
                self.x = x;
                self.y = audio[i];
            }
        }
    }
}
