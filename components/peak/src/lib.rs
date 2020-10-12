use dlal_component_base::{component, json, serde_json, Body, CmdResult};

component!(
    {"in": ["audio"], "out": ["audio"]},
    [
        {"name": "join_info", "value": {"kwargs": ["samples_per_evaluation"]}},
        "multi",
        "check_audio",
    ],
    {
        audio: Vec<f32>,
        value: f32,
    },
    {
        "value": {},
    },
);

impl ComponentTrait for Component {
    fn join(&mut self, body: serde_json::Value) -> CmdResult {
        self.audio
            .resize(body.kwarg("samples_per_evaluation")?, 0.0);
        Ok(None)
    }

    fn audio(&mut self) -> Option<&mut [f32]> {
        Some(self.audio.as_mut_slice())
    }

    fn evaluate(&mut self) {
        for i in &mut self.audio {
            self.value *= 0.999;
            if self.value < i.abs() {
                self.value = i.abs();
            }
            *i = self.value;
        }
        self.multi_audio(&self.audio);
        for i in &mut self.audio {
            *i = 0.0;
        }
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(None)
    }

    fn from_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(None)
    }
}

impl Component {
    fn value_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!(self.value)))
    }
}
