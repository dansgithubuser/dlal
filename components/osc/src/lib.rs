use dlal_component_base::{command, err, gen_component, join, json, marg, uni, Error, View};

use std::f32;

fn wave_sin(phase: f32) -> f32 {
    (phase * 2.0 * std::f32::consts::PI).sin()
}

fn wave_tri(phase: f32) -> f32 {
    if phase < 0.5 {
        phase * 4.0 - 1.0
    } else {
        -phase * 4.0 + 3.0
    }
}

fn wave_saw(phase: f32) -> f32 {
    -1.0 + 2.0 * phase
}

pub struct Specifics {
    samples_per_evaluation: usize,
    sample_rate: u32,
    wave_str: String,
    wave: fn(f32) -> f32,
    bend: f32,
    step: f32,
    phase: f32,
    output: Option<View>,
}

impl Specifics {
    fn wave_set(&mut self, wave: &str) -> Result<(), Box<Error>> {
        self.wave_str = wave.into();
        match wave {
            "sin" => self.wave = wave_sin,
            "tri" => self.wave = wave_tri,
            "saw" => self.wave = wave_saw,
            _ => return err!("unknown wave"),
        };
        Ok(())
    }
}

gen_component!(Specifics, {"in": ["midi"], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            samples_per_evaluation: 0,
            sample_rate: 0,
            wave_str: "sin".into(),
            wave: wave_sin,
            bend: 1.0,
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
        command!(
            commands,
            "wave",
            |soul, body| {
                soul.wave_set(marg!(arg_str &body, 0)?)?;
                Ok(None)
            },
            {
                "args": [{
                    "name": "wave",
                    "choices": ["sin", "tri"],
                }],
            }
        );
        command!(
            commands,
            "bend",
            |soul, body| {
                soul.bend = marg!(arg_num &body, 0)?;
                Ok(None)
            },
            {
                "args": [{
                    "name": "bend",
                    "description": "1 is no bend",
                }],
            }
        );
        command!(
            commands,
            "to_json",
            |soul, _body| {
                Ok(Some(json!({
                    "wave": soul.wave_str,
                })))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                let j = marg!(arg &body, 0)?;
                soul.wave_set(marg!(json_str marg!(json_get j, "wave")?)?)?;
                Ok(None)
            },
            { "args": ["json"] },
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
            self.phase += self.step * self.bend;
            self.phase -= self.phase.floor();
            *i += (self.wave)(self.phase);
        }
    }
}
