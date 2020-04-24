use dlal_component_base::{command, gen_component, join, json, marg, uni, View};

use std::f32;

pub struct Specifics {
    samples_per_evaluation: usize,
    sample_rate: u32,
    wave: fn(f32) -> f32,
    step: f32,
    phase: f32,
    output: Option<View>,
}

gen_component!(Specifics, {"in": ["midi"], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            samples_per_evaluation: 0,
            sample_rate: 0,
            wave: |phase| (phase * 2.0 * std::f32::consts::PI).sin(),
            step: 0.0,
            phase: 0.0,
            output: None,
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
            "freq",
            |soul, body| {
                if let Ok(freq) = marg!(arg_num &body, 0) as Result<f32, _> {
                    soul.step = freq / soul.sample_rate as f32;
                }
                Ok(Some(json!(soul.step * soul.sample_rate as f32)))
            },
            {
                "args": [{
                    "name": "freq",
                    "optional": true,
                }],
            }
        );
    }

    fn midi(&mut self, msg: &[u8]) {
        if msg.len() < 3 {
            return;
        }
        match msg[0] & 0xf0 {
            0x90 => {
                if msg[2] != 0 {
                    self.step = 440.0 * 2.0_f32.powf((msg[1] as f32 - 69.0) / 12.0)
                        / self.sample_rate as f32;
                }
            }
            _ => {}
        }
    }

    fn evaluate(&mut self) {
        for i in uni!(audio self).iter_mut() {
            self.phase += self.step;
            self.phase -= self.phase.floor();
            *i += (self.wave)(self.phase);
        }
    }
}
