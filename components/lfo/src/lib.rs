use dlal_component_base::{component, json, serde_json, Body, CmdResult};

use std::f32::consts::PI;

component!(
    {"in": [], "out": ["audio"]},
    ["run_size", "sample_rate", "uni", "check_audio"],
    {
        freq: f32,
        amp: f32,
        phase: f32,
    },
    {
        "freq": {
            "args": [{
                "name": "freq",
                "optional": true,
            }],
        },
        "amp": {
            "args": [{
                "name": "amp",
                "optional": true,
            }],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.freq = 1.0;
        self.amp = 0.1;
    }

    fn run(&mut self) {
        let step = 2.0 * PI * self.freq / self.sample_rate as f32;
        if let Some(output) = self.output.as_ref() {
            let audio = output.audio(self.run_size).unwrap();
            for i in 0..self.run_size {
                audio[i] += self.amp * self.phase.sin();
                self.phase += step;
            }
        } else {
            self.phase += step * self.run_size as f32;
        }
        if self.phase > 2.0 * PI {
            self.phase -= 2.0 * PI;
        }
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({
            "freq": self.freq,
            "amp": self.amp,
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = body.arg::<serde_json::Value>(0)?;
        self.freq = j.at("freq")?;
        self.amp = j.at("amp")?;
        Ok(None)
    }
}

impl Component {
    fn freq_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.freq = v;
        }
        Ok(Some(json!(self.freq)))
    }
    fn amp_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.amp = v;
        }
        Ok(Some(json!(self.amp)))
    }
}
