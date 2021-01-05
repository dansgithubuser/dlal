use dlal_component_base::{component, json, serde_json, Body, CmdResult};

component!(
    {"in": ["midi"], "out": ["midi"]},
    [
        "run_size",
        "sample_rate",
        "multi",
    ],
    {
        pattern: Vec<String>,
        duration: f32,
        msgs: Vec<Vec<u8>>,
        age: f32,
        i_pattern: usize,
        i_msgs: usize,
    },
    {
        "pattern": {
            "args": [
                {
                    "name": "pattern",
                    "desc": "array of strings; d for downstroke, u for upstroke",
                },
            ],
        },
        "duration": {
            "args": [
                {
                    "name": "duration",
                    "desc": "how long a strum lasts in seconds",
                },
            ],
        },
    },
);

impl Component {
    fn next_stroke(&mut self) {
        self.msgs.clear();
        self.i_msgs = 0;
        loop {
            self.i_pattern += 1;
            if self.i_pattern == self.pattern.len() {
                self.i_pattern = 0;
            }
            match self.pattern[self.i_pattern].as_str() {
                "d" | "u" => break,
                _ => (),
            }
        }
    }
}

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.pattern = vec!["d".into()];
        self.duration = 0.03;
    }

    fn run(&mut self) {
        if self.age == 0.0 {
            self.msgs.sort_by(|a, b| a[1].cmp(&b[1]));
            if self.pattern[self.i_pattern] == "u" {
                self.msgs.reverse();
            }
        }
        self.age += self.run_size as f32 / self.sample_rate as f32;
        match self.msgs.len() {
            0 => (),
            1 => {
                self.multi_midi(&self.msgs[0]);
                self.next_stroke();
            }
            _ => {
                while self.age > self.duration * self.i_msgs as f32 / (self.msgs.len() as f32 - 1.0) {
                    self.multi_midi(&self.msgs[self.i_msgs]);
                    self.i_msgs += 1;
                    if self.i_msgs == self.msgs.len() {
                        self.next_stroke();
                        break;
                    }
                }
            }
        }
    }

    fn midi(&mut self, msg: &[u8]) {
        if msg.len() < 3 || msg[0] & 0xf0 != 0x90 || msg[2] == 0 {
            self.multi_midi(msg);
            return;
        }
        self.msgs.push(msg.to_vec());
        self.age = 0.0;
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({
            "pattern": self.pattern,
            "duration": self.duration,
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = body.arg::<serde_json::Value>(0)?;
        self.pattern = j.at("pattern")?;
        self.duration = j.at("duration")?;
        Ok(None)
    }
}

impl Component {
    fn pattern_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg::<Vec<_>>(0) {
            if v.len() == 0 {
                self.pattern = vec!["d".into()];
            } else {
                self.pattern = v;
            }
        }
        Ok(Some(json!(self.pattern)))
    }

    fn duration_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.duration = v;
        }
        Ok(Some(json!(self.duration)))
    }
}
