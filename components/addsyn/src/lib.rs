use dlal_component_base::{arg, Body, CmdResult, component, json, serde_json};
use serde::{Serialize, Deserialize};

//===== partial =====//
#[derive(Clone, Debug, Deserialize, Serialize)]
struct Partial {
    v: f32,  // volume
    a: f32,  // attack
    d: f32,  // decay
    s: f32,  // sustain
    r: f32,  // release
    m: f32,  // freq multiplier
    b: f32,  // freq offset
}

arg!(Partial);

//===== decay mode =====//
#[derive(Copy, Clone, Debug, Deserialize, Serialize)]
enum DecayMode {
    Linear,
    Exponential,
}

impl Default for DecayMode {
    fn default() -> Self {
        DecayMode::Linear
    }
}

arg!(DecayMode);

//===== runner =====//
#[derive(Debug, PartialEq)]
enum Stage {
    A, //attack
    D, //decay
    S, //sustain
    R, //release
}

#[derive(Debug)]
struct Runner {
    phase: f32,
    stage: Stage,
    vol: f32, // envelope amplitude
    partial: Partial,
    decay_mode: DecayMode,
}

impl Runner {
    fn new(partial: &Partial, decay_mode: DecayMode, sample_rate: f32) -> Self {
        Self {
            phase: 0.0,
            stage: Stage::R,
            vol: 0.0,
            partial: Partial {
                v: partial.v,
                a: partial.a / sample_rate,
                d: match decay_mode {
                    DecayMode::Linear => partial.d / sample_rate,
                    DecayMode::Exponential => 10.0_f32.powf(-partial.d / sample_rate / 20.0),
                },
                s: partial.s,
                r: partial.r / sample_rate,
                m: partial.m,
                b: partial.b / sample_rate,
            },
            decay_mode,
        }
    }

    fn advance_envelope(&mut self) {
        match self.stage {
            Stage::A => {
                self.vol += self.partial.a;
                if self.vol > 1.0 {
                    self.vol = 1.0;
                    self.stage = Stage::D;
                }
            }
            Stage::D => {
                match self.decay_mode {
                    DecayMode::Linear => {
                        self.vol -= self.partial.d;
                    }
                    DecayMode::Exponential => {
                        self.vol *= self.partial.d;
                    }
                }
                if self.vol < self.partial.s {
                    self.vol = self.partial.s;
                    self.stage = Stage::S;
                }
            }
            Stage::S => (),
            Stage::R => {
                self.vol -= self.partial.r;
                if self.vol < 0.0 {
                    self.vol = 0.0;
                }
            }
        }
    }
}

//===== note =====//
struct Note {
    runners: Vec<Runner>,
    step: f32,
    vel: f32,
}

impl Note {
    fn new(freq: f32, sample_rate: u32) -> Self {
        Note {
            runners: Vec::new(),
            step: freq / sample_rate as f32,
            vel: 0.0,
        }
    }

    fn on(&mut self, vel: f32) {
        self.vel = vel;
        for runner in self.runners.iter_mut() {
            runner.phase = 0.0;
            runner.stage = Stage::A;
        }
    }

    fn off(&mut self, _vel: f32) {
        for runner in self.runners.iter_mut() {
            runner.stage = Stage::R;
        }
    }

    fn advance(&mut self, bend: f32) -> f32 {
        let mut x = 0.0;
        for runner in self.runners.iter_mut() {
            runner.advance_envelope();
            x += self.vel * runner.partial.v * runner.vol * (runner.phase * std::f32::consts::TAU).sin();
            runner.phase += self.step * runner.partial.m * bend + runner.partial.b;
            if runner.phase > 1.0 {
                runner.phase -= 1.0;
            }
        }
        x
    }

    fn done(&self) -> bool {
        for runner in self.runners.iter() {
            if runner.stage != Stage::R || runner.vol > 1e-6{
                return false;
            }
        }
        true
    }
}

//===== component =====//
component!(
    {"in": ["midi"], "out": ["audio"]},
    [
        "run_size",
        "sample_rate",
        "uni",
        "check_audio",
        {"name": "field_helpers", "fields": ["partials", "decay_mode"], "kinds": ["json"]},
        "midi_rpn",
        "midi_bend",
        "notes",
    ],
    {
        partials: Vec<Partial>,
        decay_mode: DecayMode,
    },
    {
        "partials": {
            "args": [
                {
                    "name": "partials",
                    "type": "array",
                    "element": {
                        "name": "partial",
                        "type": "dict",
                        "keys": [
                            {
                                "name": "v",
                                "desc": "volume",
                                "range": "[0, 1]",
                            },
                            {
                                "name": "a",
                                "desc": "attack rate",
                                "units": "amplitude per second",
                                "range": "(0, 1]",
                            },
                            {
                                "name": "d",
                                "desc": "decay rate",
                                "units": "amplitude per second or dB/s",
                                "range": "(0, 1] or [0, inf)",
                            },
                            {
                                "name": "s",
                                "desc": "sustain level",
                                "range": "[0, 1]",
                            },
                            {
                                "name": "r",
                                "desc": "release rate",
                                "units": "amplitude per second",
                                "range": "(0, 1]",
                            },
                            {
                                "name": "m",
                                "desc": "frequency multiplier",
                            },
                            {
                                "name": "b",
                                "units": "Hz",
                                "desc": "frequency offset",
                            },
                        ],
                    },
                },
            ],
        },
        "decay_mode": {
            "args": [
                {
                    "name": "mode",
                    "options": [
                        "Linear",
                        "Exponential",
                    ],
                },
            ],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.partials.push(Partial {
            v: 1.0,
            a: 1e-3,
            d: 1e-5,
            s: 0.5,
            r: 1e-4,
            m: 1.0,
            b: 0.0,
        });
    }

    fn join(&mut self, _body: serde_json::Value) -> CmdResult {
        self.update_note_partials();
        Ok(None)
    }

    fn run(&mut self) {
        self.note_run_uni();
    }

    fn midi(&mut self, msg: &[u8]) {
        if msg.len() < 3 {
            return;
        }
        match msg[0] & 0xf0 {
            0x80 => self.note_off(msg),
            0x90 => self.note_on(msg),
            0xb0 => self.midi_rpn(msg),
            0xe0 => self.midi_bend(msg),
            _ => {}
        }
    }
}

impl Component {
    fn partials_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        match body.arg(0) {
            Ok(v) => self.partials = v,
            e => if body.has_arg(0) {
                e?;
            }
        }
        self.update_note_partials();
        Ok(Some(json!(self.partials)))
    }

    fn decay_mode_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        match body.arg(0) {
            Ok(v) => self.decay_mode = v,
            e => if body.has_arg(0) {
                e?;
            }
        }
        self.update_note_partials();
        Ok(Some(json!(self.decay_mode)))
    }

    fn update_note_partials(&mut self) {
        for note in self.notes.iter_mut() {
            note.runners = self.partials
                .iter()
                .map(|i| Runner::new(i, self.decay_mode, self.sample_rate as f32))
                .collect();
        }
    }
}
