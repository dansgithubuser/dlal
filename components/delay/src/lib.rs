use dlal_component_base::{component, json, serde_json, Body, CmdResult};

component!(
    {"in": [], "out": ["audio"]},
    [
        "run_size",
        "uni",
        "check_audio",
        {"name": "field_helpers", "fields": ["gain_x", "gain_y", "gain_i", "gain_o"], "kinds": ["rw", "json"]},
    ],
    {
        gain_x: f32,
        gain_y: f32,
        gain_i: f32,
        gain_o: f32,
        audio: Vec<f32>,
        index: usize,
    },
    {
        "resize": {
            "args": [{
                "name": "size",
                "optional": true,
            }],
        },
        "gain_x": {
            "args": [{
                "name": "gain_x",
                "optional": true,
                "desc": "input tap amount",
                "default": "1.0",
            }],
        },
        "gain_y": {
            "args": [{
                "name": "gain_y",
                "optional": true,
                "desc": "output tap amount (feedback)",
                "default": "0.0",
            }],
        },
        "gain_i": {
            "args": [{
                "name": "gain_i",
                "optional": true,
                "desc": "monitor amount",
                "default": "0.0",
            }],
        },
        "gain_o": {
            "args": [{
                "name": "gain_o",
                "optional": true,
                "desc": "output amount",
                "default": "1.0",
            }],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.gain_x = 1.0;
        self.gain_o = 1.0;
        self.audio.resize(22050, 0.0);
    }

    fn run(&mut self) {
        let audio = match &self.output {
            Some(output) => output.audio(self.run_size).unwrap(),
            None => return,
        };
        for i in 0..self.run_size {
            let x = audio[i];
            let y = self.audio[self.index];
            audio[i] = x * self.gain_i + y * self.gain_o;
            self.audio[self.index] = x * self.gain_x + y * self.gain_y;
            self.index += 1;
            self.index %= self.audio.len();
        }
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(field_helper_to_json!(self, {
            "size": self.audio.len(),
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = field_helper_from_json!(self, body);
        self.audio.resize(j.at("size")?, 0.0);
        Ok(None)
    }
}

impl Component {
    fn resize_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.audio.resize(v, 0.0);
        }
        Ok(Some(json!(self.audio.len())))
    }
}
