use dlal_component_base::{component, err, json, serde_json, Body, CmdResult, Error};

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
    let t = time::SystemTime::now()
        .duration_since(time::UNIX_EPOCH)
        .unwrap();
    let r1 = t.as_secs();
    let r2 = t.subsec_nanos() as u64;
    let r3 = unsafe { *std::mem::transmute::<*const f32, *const u32>(&phase) } as u64;
    const PERIOD: u64 = 77777;
    let rf = (r1 ^ r2 ^ r3) % PERIOD;
    2.0 * rf as f32 / PERIOD as f32 - 1.0
}

struct Wave {
    f: fn(f32) -> f32,
    name: String,
}

impl Default for Wave {
    fn default() -> Self {
        Self {
            f: wave_sin,
            name: "sin".into(),
        }
    }
}

component!(
    {"in": ["midi"], "out": ["audio"]},
    ["samples_per_evaluation", "sample_rate", "uni", "check_audio"],
    {
        wave_str: String,
        wave: Wave,
        bend: f32,
        step: f32,
        phase: f32,
        vol: f32,
    },
    {
        "freq": {
            "args": [{
                "name": "freq",
                "optional": true,
            }],
        },
        "wave": {
            "args": [{
                "name": "wave",
                "choices": ["sin", "tri", "saw", "noise"],
            }],
        },
        "bend": {
            "args": [{
                "name": "bend",
                "description": "1 is no bend",
            }],
        },
        "phase": {
            "args": [{
                "name": "phase",
                "range": "[0..1)",
            }],
        },
    },
);

impl Component {
    fn wave_set(&mut self, wave: &str) -> Result<(), Box<Error>> {
        self.wave.name = wave.into();
        match wave {
            "sin" => self.wave.f = wave_sin,
            "tri" => self.wave.f = wave_tri,
            "saw" => self.wave.f = wave_saw,
            "noise" => self.wave.f = wave_noise,
            _ => return Err(err!("unknown wave").into()),
        };
        Ok(())
    }
}

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.samples_per_evaluation = 64;
        self.sample_rate = 44100;
        self.vol = 1.0;
        self.bend = 1.0;
    }

    fn midi(&mut self, msg: &[u8]) {
        if msg.len() < 3 {
            return;
        }
        match msg[0] & 0xf0 {
            0x90 => {
                self.step =
                    440.0 * 2.0_f32.powf((msg[1] as f32 - 69.0) / 12.0) / self.sample_rate as f32;
                self.vol = msg[2] as f32 / 127.0;
            }
            0x80 => {
                self.vol = 0.0;
            }
            _ => {}
        }
    }

    fn evaluate(&mut self) {
        if let Some(output) = self.output.as_ref() {
            for i in output.audio(self.samples_per_evaluation).unwrap() {
                self.phase += self.step * self.bend;
                self.phase -= self.phase.floor();
                *i += self.vol * (self.wave.f)(self.phase);
            }
        }
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({
            "wave": self.wave.name,
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = body.arg::<serde_json::Value>(0)?;
        self.wave_set(&j.at::<String>("wave")?)?;
        Ok(None)
    }
}

impl Component {
    fn freq_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(freq) = body.arg::<f32>(0) {
            self.step = freq / self.sample_rate as f32;
        }
        Ok(Some(json!(self.step * self.sample_rate as f32)))
    }

    fn wave_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.wave_set(&body.arg::<String>(0)?)?;
        Ok(None)
    }

    fn bend_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.bend = body.arg(0)?;
        Ok(None)
    }

    fn phase_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.phase = body.arg(0)?;
        Ok(None)
    }
}
