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

#[derive(Debug, PartialEq)]
enum Stage {
    A, //attack
    D, //decay
    S, //sustain
    R, //release
}

#[derive(Debug)]
struct PartialState {
    phase: f32,
    stage: Stage,
    vol: f32, // envelope amplitude
    b: f32,
}

impl PartialState {
    fn new() -> Self {
        Self {
            phase: 0.0,
            stage: Stage::R,
            vol: 0.0,
            b: 0.0,
        }
    }

    fn advance_envelope(&mut self, partial: &Partial) {
        match self.stage {
            Stage::A => {
                self.vol += partial.a;
                if self.vol > 1.0 {
                    self.vol = 1.0;
                    self.stage = Stage::D;
                }
            }
            Stage::D => {
                self.vol -= partial.d;
                if self.vol < partial.s {
                    self.vol = partial.s;
                    self.stage = Stage::S;
                }
            }
            Stage::S => (),
            Stage::R => {
                self.vol -= partial.r;
                if self.vol < 0.0 {
                    self.vol = 0.0;
                }
            }
        }
    }
}

//===== note =====//
struct Note {
    sample_rate: f32,
    partials: Vec<(Partial, PartialState)>,
    step: f32,
    vel: f32,
}

impl Note {
    fn new(freq: f32, sample_rate: u32) -> Self {
        Note {
            sample_rate: sample_rate as f32,
            partials: Vec::new(),
            step: freq / sample_rate as f32,
            vel: 0.0,
        }
    }

    fn on(&mut self, vel: f32) {
        self.vel = vel;
        for (partial, state) in self.partials.iter_mut() {
            state.b = partial.b / self.sample_rate;
            state.phase = 0.0;
            state.stage = Stage::A;
        }
    }

    fn off(&mut self, _vel: f32) {
        for (_, state) in self.partials.iter_mut() {
            state.stage = Stage::R;
        }
    }

    fn advance(&mut self, bend: f32) -> f32 {
        let mut x = 0.0;
        for (partial, state) in self.partials.iter_mut() {
            state.advance_envelope(&partial);
            x += self.vel * partial.v * state.vol * (state.phase * std::f32::consts::TAU).sin();
            state.phase += self.step * partial.m * bend + state.b;
            if state.phase > 1.0 {
                state.phase -= 1.0;
            }
        }
        x
    }

    fn done(&self) -> bool {
        for (_, state) in self.partials.iter() {
            if state.stage != Stage::R || state.vol > 1e-6{
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
        {"name": "field_helpers", "fields": ["partials"], "kinds": ["json"]},
        "midi_rpn",
        "midi_bend",
        "notes",
    ],
    {
        partials: Vec<Partial>,
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
                                "units": "amplitude per sample",
                                "range": "(0, 1]",
                            },
                            {
                                "name": "d",
                                "desc": "decay rate",
                                "units": "amplitude per sample",
                                "range": "(0, 1]",
                            },
                            {
                                "name": "s",
                                "desc": "sustain level",
                                "range": "[0, 1]",
                            },
                            {
                                "name": "r",
                                "desc": "release rate",
                                "units": "amplitude per sample",
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

    fn update_note_partials(&mut self) {
        for note in self.notes.iter_mut() {
            note.partials = self.partials
                .iter()
                .map(|i| (
                    i.clone(),
                    PartialState::new(),
                ))
                .collect();
        }
    }
}
