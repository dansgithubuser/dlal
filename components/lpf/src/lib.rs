use dlal_component_base::{arg_num, command, gen_component, join, json, uni, View};

use std::f32::consts::PI;

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    sample_rate: u32,
    a: f32,
    y: f32,
    output: Option<View>,
}

gen_component!(Specifics, {"in": [], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            a: 0.95,
            ..Default::default()
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                join!(samples_per_evaluation soul, body);
                join!(sample_rate soul, body);
                Ok(None)
            },
            ["samples_per_evaluation", "sample_rate"],
        );
        uni!(connect commands, true);
        command!(
            commands,
            "set",
            |soul, body| {
                if let Ok(lowness) = arg_num::<f32>(&body, 0) {
                    soul.a = 1.0 - lowness;
                }
                Ok(Some(json!(1.0 - soul.a)))
            },
            {
                "args": [{
                    "name": "lowness",
                    "optional": true,
                    "range": "[0, 1]",
                }],
            }
        );
        command!(
            commands,
            "freq",
            |soul, body| {
                if let Ok(sample_rate) = arg_num::<u32>(&body, 1) {
                    soul.sample_rate = sample_rate;
                }
                if let Ok(freq) = arg_num::<f32>(&body, 0) {
                    soul.a = 1.0 / (1.0 + 1.0 / (2.0 * PI / soul.sample_rate as f32 * freq));
                }
                Ok(Some(json!(1.0 / (1.0 / soul.a - 1.0) / (2.0 * PI * soul.sample_rate as f32))))
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
            |soul, _body| { Ok(Some(json!(soul.a.to_string()))) },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                soul.a = arg_num(&body, 0)?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        if let Some(output) = &self.output {
            let audio = output.audio(self.samples_per_evaluation).unwrap();
            for i in 0..self.samples_per_evaluation {
                audio[i] = self.y + self.a * (audio[i] - self.y);
                self.y = audio[i];
            }
        }
    }
}
