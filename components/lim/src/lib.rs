use dlal_component_base::{component, json, serde_json, Body, CmdResult};

component!(
    {"in": [], "out": ["audio"]},
    ["run_size", "multi", "check_audio"],
    {
        soft: f32,
        soft_gain: f32,
        hard: f32,
    },
    {
        "soft": {
            "args": [{
                "name": "soft",
                "optional": true,
            }],
        },
        "soft_gain": {
            "args": [{
                "name": "soft_gain",
                "optional": true,
            }],
        },
        "hard": {
            "args": [{
                "name": "hard",
                "optional": true,
            }],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.soft = 0.4;
        self.soft_gain = 0.5;
        self.hard = 0.5;
    }

    fn run(&mut self) {
        for output in &self.outputs {
            let audio = output.audio(self.run_size).unwrap();
            for i in audio {
                if *i > self.soft {
                    *i = self.soft + (*i - self.soft) * self.soft_gain;
                    if *i > self.hard {
                        *i = self.hard;
                    }
                } else if *i < -self.soft {
                    *i = -self.soft + (*i + self.soft) * self.soft_gain;
                    if *i < -self.hard {
                        *i = -self.hard;
                    }
                }
            }
        }
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({
            "soft": self.soft,
            "soft_gain": self.soft_gain,
            "hard": self.hard,
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = body.arg::<serde_json::Value>(0)?;
        self.soft = j.at("soft")?;
        self.soft_gain = j.at("soft_gain")?;
        self.hard = j.at("hard")?;
        Ok(None)
    }
}

impl Component {
    fn soft_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.soft = v;
        }
        Ok(Some(json!(self.soft)))
    }

    fn soft_gain_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.soft_gain = v;
        }
        Ok(Some(json!(self.soft_gain)))
    }

    fn hard_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.hard = v;
            if self.soft > self.hard {
                self.soft = self.hard;
            }
        }
        Ok(Some(json!(self.hard)))
    }
}
