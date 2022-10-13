use dlal_component_base::{component, CmdResult, json, serde_json};

component!(
    {"in": ["audio"], "out": ["audio"]},
    [
        {"name": "join_info", "kwargs": ["run_size"]},
        "multi",
        "audio",
        "check_audio",
        {"name": "field_helpers", "fields": ["decay"], "kinds": ["rw", "json"]},
    ],
    {
        lo: f32,
        hi: f32,
        decay: f32,
    },
    {
        "value": {"args": []},
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.decay = 0.999;
    }

    fn run(&mut self) {
        for i in &mut self.audio {
            self.lo *= self.decay;
            self.hi *= self.decay;
            if *i < self.lo {
                self.lo = *i;
            }
            if *i > self.hi {
                self.hi = *i;
            }
            *i = self.hi - self.lo;
        }
        self.multi_audio(&self.audio);
        for i in &mut self.audio {
            *i = 0.0;
        }
    }
}

impl Component {
    fn value_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!(self.hi - self.lo)))
    }
}
