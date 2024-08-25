use dlal_component_base::{component, json, serde_json, Body, CmdResult};

component!(
    {"in": ["midi"], "out": ["audio"]},
    [
        "run_size",
        "uni",
        {
            "name": "field_helpers",
            "fields": ["amount_dst", "smooth"],
            "kinds": ["rw", "json"]
        },
    ],
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
        self.amount = self.smooth * self.amount + (1.0 - self.smooth) * self.amount_dst;
        if let Some(output) = &self.output {
            for i in output.audio(self.run_size).unwrap() {
                *i *= self.amount;
            }
        }
    }

    fn midi(&mut self, msg: &[u8]) {
        if msg.len() < 3 {
            return;
        }
        match msg[0] & 0xf0 {
            0x90 => {
                self.amount_dst = msg[2] as f32 / 127.0;
            }
            0xa0 => {
                self.amount_dst = msg[2] as f32 / 127.0;
            }
            _ => (),
        };
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
