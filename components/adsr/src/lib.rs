use dlal_component_base::{component, serde_json, CmdResult};

enum Stage {
    A,
    D,
    S,
    R,
}

impl Default for Stage {
    fn default() -> Self {
        Stage::R
    }
}

component!(
    {"in": ["midi"], "out": ["audio"]},
    [
        "uni",
        "check_audio",
        "run_size",
        {"name": "field_helpers", "fields": ["a", "d", "s", "r"], "kinds": ["rw", "json"]},
    ],
    {
        a: f32,
        d: f32,
        s: f32,
        r: f32,
        stage: Stage,
        vol: f32,
    },
    {
        "a": {
            "args": [{
                "name": "amount",
                "desc": "attack rate",
                "units": "amplitude per sample",
                "range": "(0, 1]",
            }],
        },
        "d": {
            "args": [{
                "name": "amount",
                "desc": "decay rate",
                "units": "amplitude per sample",
                "range": "(0, 1]",
            }],
        },
        "s": {
            "args": [{
                "name": "amount",
                "desc": "sustain level",
                "range": "[0, 1]",
            }],
        },
        "r": {
            "args": [{
                "name": "amount",
                "desc": "release rate",
                "units": "amplitude per sample",
                "range": "(0, 1]",
            }],
        },
        "reset": {},
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.a = 0.01;
        self.d = 0.01;
        self.s = 0.5;
        self.r = 0.01;
    }

    fn run(&mut self) {
        let audio = match &self.output {
            Some(output) => output.audio(self.run_size).unwrap(),
            None => return,
        };
        for i in audio {
            match self.stage {
                Stage::A => {
                    self.vol += self.a;
                    if self.vol > 1.0 {
                        self.vol = 1.0;
                        self.stage = Stage::D;
                    }
                }
                Stage::D => {
                    self.vol -= self.d;
                    if self.vol < self.s {
                        self.vol = self.s;
                        self.stage = Stage::S;
                    }
                }
                Stage::S => (),
                Stage::R => {
                    self.vol -= self.r;
                    if self.vol < 0.0 {
                        self.vol = 0.0;
                    }
                }
            }
            *i *= self.vol;
        }
    }

    fn midi(&mut self, msg: &[u8]) {
        if msg.len() < 3 {
            return;
        }
        let type_nibble = msg[0] & 0xf0;
        if type_nibble == 0x80 || type_nibble == 0x90 && msg[2] == 0 {
            self.stage = Stage::R;
        } else if type_nibble == 0x90 {
            self.stage = Stage::A;
        }
    }
}

impl Component {
    fn reset_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        self.stage = Stage::R;
        self.vol = 0.0;
        Ok(None)
    }
}
