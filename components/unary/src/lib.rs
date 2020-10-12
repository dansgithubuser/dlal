use dlal_component_base::{component, json, serde_json, Body, CmdResult};

component!(
    {"in": [], "out": ["audio"]},
    ["samples_per_evaluation", "multi", "check_audio"],
    {
        mode: String,
    },
    {
        "mode": {
            "args": [{
                "name": "mode",
                "optional": true,
                "choices": ["exp2", "sqrt"],
            }],
        },
    },
);

impl ComponentTrait for Component {
    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({
            "mode": self.mode,
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = body.arg::<serde_json::Value>(0)?;
        self.mode = j.at("mode")?;
        Ok(None)
    }

    fn evaluate(&mut self) {
        for output in &self.outputs {
            for i in output.audio(self.samples_per_evaluation).unwrap() {
                *i = match self.mode.as_str() {
                    "exp2" => i.exp2(),
                    "sqrt" => {
                        if *i >= 0.0 {
                            i.sqrt()
                        } else {
                            -(-*i).sqrt()
                        }
                    }
                    _ => *i,
                }
            }
        }
    }
}

impl Component {
    fn mode_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.mode = v;
        }
        Ok(Some(json!(self.mode)))
    }
}
