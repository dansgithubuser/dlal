use dlal_component_base::{component, json, serde_json, Body, CmdResult};

use std::f32::consts::PI;

component!(
    {"in": [], "out": ["audio"]},
    ["samples_per_evaluation", "sample_rate", "uni", "check_audio"],
    {
        a: f32,
        x: f32,
        y: f32,
    },
    {
        "set": {
            "args": [{
                "name": "highness",
                "optional": true,
                "range": "[0, 1]",
            }],
        },
        "freq": {
            "args": [
                {
                    "name": "freq",
                    "optional": true,
                },
                {
                    "name": "sample_rate",
                    "optional": true,
                },
            ],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.a = 0.05;
    }

    fn evaluate(&mut self) {
        if let Some(output) = &self.output {
            let audio = output.audio(self.samples_per_evaluation).unwrap();
            for i in 0..self.samples_per_evaluation {
                let x = audio[i];
                audio[i] = self.a * (self.y + x - self.x);
                self.x = x;
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
        if let Ok(highness) = body.arg::<f32>(0) {
            self.a = 1.0 - highness;
        }
        Ok(Some(json!(1.0 - self.a)))
    }

    fn freq_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(sample_rate) = body.arg(1) {
            self.sample_rate = sample_rate;
        }
        if let Ok(freq) = body.arg::<f32>(0) {
            self.a = 1.0 / (2.0 * PI / self.sample_rate as f32 * freq + 1.0);
        }
        Ok(Some(json!(
            (1.0 / self.a - 1.0) / (2.0 * PI / self.sample_rate as f32)
        )))
    }
}
