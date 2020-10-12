use dlal_component_base::{component, json, serde_json, Body, CmdResult};

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
    ["uni", "check_audio", "samples_per_evaluation"],
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

    fn evaluate(&mut self) {
        let audio = match &self.output {
            Some(output) => output.audio(self.samples_per_evaluation).unwrap(),
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
            *i += self.vol;
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

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({
            "a": self.a,
            "d": self.d,
            "s": self.s,
            "r": self.r,
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j: serde_json::Value = body.arg(0)?;
        self.a = j.at("a")?;
        self.d = j.at("d")?;
        self.s = j.at("s")?;
        self.r = j.at("r")?;
        Ok(None)
    }
}

impl Component {
    fn a_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.a = v;
        }
        Ok(Some(json!(self.a)))
    }

    fn d_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.d = v;
        }
        Ok(Some(json!(self.d)))
    }

    fn s_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.s = v;
        }
        Ok(Some(json!(self.s)))
    }

    fn r_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.r = v;
        }
        Ok(Some(json!(self.r)))
    }

    fn reset_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        self.stage = Stage::R;
        self.vol = 0.0;
        Ok(None)
    }
}
