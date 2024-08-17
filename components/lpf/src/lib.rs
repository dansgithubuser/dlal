use dlal_component_base::{component, json, serde_json, Body, CmdResult};

use std::f32::consts::PI;

component!(
    {"in": [], "out": ["audio"]},
    ["run_size", "sample_rate", "uni", "check_audio"],
    {
        a: f32,
        y: f32,
    },
    {
        "set": {
            "args": [{
                "name": "lowness",
                "optional": true,
                "range": "[0, 1]",
                "default": 0.95,
            }],
        },
        "get": {},
        "freq": {
            "args": [
                {"name": "freq", "optional": true},
                {"name": "sample_rate", "optional": true},
            ],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.a = 0.95;
    }

    fn run(&mut self) {
        if let Some(output) = &self.output {
            let audio = output.audio(self.run_size).unwrap();
            for i in 0..self.run_size {
                audio[i] = self.y + self.a * (audio[i] - self.y);
                self.y = audio[i];
            }
        }
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!(self.a)))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.a = body.arg(0)?;
        Ok(None)
    }
}

impl Component {
    fn set_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(lowness) = body.arg::<f32>(0) {
            self.a = 1.0 - lowness;
        }
        Ok(Some(json!(1.0 - self.a)))
    }

    fn get_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!(1.0 - self.a)))
    }

    fn freq_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(sample_rate) = body.arg(1) {
            self.sample_rate = sample_rate;
        }
        if let Ok(freq) = body.arg::<f32>(0) {
            self.a = 1.0 / (1.0 + 1.0 / (2.0 * PI / self.sample_rate as f32 * freq));
        }
        Ok(Some(json!(
            1.0 / (1.0 / self.a - 1.0) / (2.0 * PI * self.sample_rate as f32)
        )))
    }
}
