use dlal_component_base::{component, json, serde_json, Body, CmdResult};

struct Ring {
    vec: Vec<f32>,
    i: usize,
}

impl Ring {
    fn new(size: usize) -> Self {
        Self {
            vec: vec![0.0; size],
            i: 0,
        }
    }

    fn write(&mut self, value: f32) {
        self.vec[self.i] = value;
        self.i += 1;
        self.i %= self.vec.len();
    }

    fn read(&self) -> f32 {
        self.vec[self.i]
    }
}

component!(
    {"in": [], "out": ["audio"]},
    [
        "run_size",
        "uni",
        "check_audio",
        {"name": "field_helpers", "fields": ["amount"], "kinds": ["json"]},
    ],
    {
        amount: f32,
        rings: Vec<Ring>,
    },
    {
        "set": { "args": ["amount"] },
        "get": {},
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.amount = 0.5;
        self.rings.push(Ring::new(1921));
        self.rings.push(Ring::new(5240));
        self.rings.push(Ring::new(5606));
        self.rings.push(Ring::new(6152));
        self.rings.push(Ring::new(6198));
        self.rings.push(Ring::new(6342));
        self.rings.push(Ring::new(7965));
        self.rings.push(Ring::new(12965));
    }

    fn run(&mut self) {
        if let Some(output) = &self.output {
            for i in output.audio(self.run_size).unwrap() {
                for j in 0..self.rings.len() {
                    *i += self.rings[j].read() * self.amount / (8 + j) as f32;
                }
                for ring in &mut self.rings {
                    ring.write(*i);
                }
            }
        }
    }
}

impl Component {
    fn set_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.amount = body.arg(0)?;
        Ok(None)
    }

    fn get_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!(self.amount)))
    }
}
