use dlal_component_base::{command, gen_component, join, json, uni, Error, View, Body, serde_json};

use std::f32;
use std::time;

fn wave_sin(phase: f32) -> f32 {
    (phase * 2.0 * f32::consts::PI).sin()
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

fn wave_noise(phase: f32) -> f32 {
    let t = time::SystemTime::now().duration_since(time::UNIX_EPOCH).unwrap();
    let r1 = t.as_secs();
    let r2 = t.subsec_nanos() as u64;
    let r3 = unsafe {
        *std::mem::transmute::<*const f32, *const u32>(&phase)
    } as u64;
    const PERIOD: u64 = 77777;
    let rf = (r1 ^ r2 ^ r3) % PERIOD;
    2.0 * rf as f32 / PERIOD as f32 - 1.0
}

pub struct Specifics {
    samples_per_evaluation: usize,
    sample_rate: u32,
    wave_str: String,
    wave: fn(f32) -> f32,
    bend: f32,
    step: f32,
    phase: f32,
    vol: f32,
    output: Option<View>,
}

impl Specifics {
    fn wave_set(&mut self, wave: &str) -> Result<(), Box<Error>> {
        self.wave_str = wave.into();
        match wave {
            "sin" => self.wave = wave_sin,
            "tri" => self.wave = wave_tri,
            "saw" => self.wave = wave_saw,
            "noise" => self.wave = wave_noise,
            _ => Error::err("unknown wave")?,
        };
        Ok(())
    }
}

gen_component!(Specifics, {"in": ["midi"], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            samples_per_evaluation: 64,
            sample_rate: 44100,
            wave_str: "sin".into(),
            wave: wave_sin,
            vol: 1.0,
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
                soul.samples_per_evaluation = body.kwarg("samples_per_evaluation")?;
                soul.sample_rate = body.kwarg("sample_rate")?;
                Ok(None)
            },
            ["samples_per_evaluation", "sample_rate"],
        );
        uni!(connect commands, true);
        command!(
            commands,
            "freq",
            |soul, body| {
                if let Ok(freq) = body.arg::<f32>(0) {
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
                soul.wave_set(&body.arg::<String>(0)?)?;
                Ok(None)
            },
            {
                "args": [{
                    "name": "wave",
                    "choices": ["sin", "tri", "saw", "noise"],
                }],
            }
        );
        command!(
            commands,
            "bend",
            |soul, body| {
                soul.bend = body.arg(0)?;
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
            "phase",
            |soul, body| {
                soul.phase = body.arg(0)?;
                Ok(None)
            },
            {
                "args": [{
                    "name": "phase",
                    "range": "[0..1)",
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
                let j = body.arg::<serde_json::Value>(0)?;
                soul.wave_set(&j.at::<String>("wave")?)?;
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
                self.step = 440.0 * 2.0_f32.powf((msg[1] as f32 - 69.0) / 12.0)
                    / self.sample_rate as f32;
                self.vol = msg[2] as f32 / 127.0;
            }
            0x80 => {
                self.vol = 0.0;
            }
            _ => {}
        }
    }

    fn evaluate(&mut self) {
        for i in uni!(audio self).iter_mut() {
            self.phase += self.step * self.bend;
            self.phase -= self.phase.floor();
            *i += self.vol * (self.wave)(self.phase);
        }
    }
}
