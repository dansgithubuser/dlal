use dlal_component_base::{component, json, serde_json, Body, CmdResult};

component!(
    {"in": [], "out": ["audio"]},
    ["run_size", "uni"],
    {
        amount: f32,
        amount_dst: f32,
        smooth: f32,
    },
    {
        "set": {"args": ["gain", "smooth"]},
        "get": {},
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.amount = 1.0;
        self.amount_dst = 1.0;
    }

    fn run(&mut self) {
        if let Some(output) = &self.output {
            for i in output.audio(self.run_size).unwrap() {
                *i *= self.amount;
            }
        }
        self.amount = self.smooth * self.amount + (1.0 - self.smooth) * self.amount_dst;
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!(self.amount)))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.amount = body.arg(0)?;
        Ok(None)
    }
}

impl Component {
    fn set_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.amount_dst = body.arg(0)?;
        self.smooth = body.arg(1).unwrap_or(0.0);
        if self.smooth == 0.0 {
            self.amount = self.amount_dst;
        }
        Ok(None)
    }

    fn get_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!(self.amount)))
    }
}
