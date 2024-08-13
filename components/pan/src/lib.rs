use dlal_component_base::{component, json, serde_json, Body, CmdResult};

component!(
    {"in": [], "out": ["audio"]},
    [
        "run_size",
        "sample_rate",
        "uni",
        "check_audio",
        {"name": "field_helpers", "fields": ["gain"], "kinds": ["rw", "json"]},
        {"name": "field_helpers", "fields": ["delay"], "kinds": ["json"]},
    ],
    {
        gain: f32,
        delay: usize,
        buf: Vec<f32>,
        buf_i: usize,
    },
    {
        "delay": {
            "args": [
                {
                    "name": "samples",
                    "optional": true,
                },
            ],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.gain = 1.0;
        self.delay = 1;
        self.buf.resize(1, 0.0);
        self.buf_i = 0;
    }

    fn run(&mut self) {
        let output = match self.output.as_ref() {
            Some(v) => v,
            None => return,
        };
        for i in output.audio(self.run_size).unwrap() {
            self.buf[self.buf_i] = *i;
            self.buf_i += 1;
            self.buf_i %= self.delay;
            *i = self.gain * self.buf[self.buf_i];
        }
    }
}

impl Component {
    fn delay_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let sample_rate = if self.sample_rate != 0 {
            self.sample_rate
        } else {
            body.kwarg("sample_rate")?
        };
        match body.arg::<f32>(0) {
            Ok(v) => {
                self.delay = (v * sample_rate as f32) as usize + 1;
                self.buf.resize(self.delay, 0.0);
                if self.buf_i >= self.delay {
                    self.buf_i = 0;
                }
            }
            e => if body.has_arg(0) {
                e?;
            }
        }
        Ok(Some(json!(self.delay as f32 / self.sample_rate as f32)))
    }
}
