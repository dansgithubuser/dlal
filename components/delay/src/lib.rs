use dlal_component_base::{component, json, serde_json, Body, CmdResult};

#[derive(Default)]
struct Smoother {
    a: f32,
    b: f32,
}

impl Smoother {
    fn smooth(&mut self, dst: f32, smoothness: f32) {
        self.a = smoothness * self.a + (1.0 - smoothness) * dst;
        self.b = smoothness * self.b + (1.0 - smoothness) * self.a;
    }
}

component!(
    {"in": [], "out": ["audio"]},
    [
        "run_size",
        "uni",
        "check_audio",
        {
            "name": "field_helpers",
            "fields": [
                "gain_x",
                "gain_y",
                "gain_i",
                "gain_o",
                "smooth"
            ],
            "kinds": ["rw", "json"]
        },
    ],
    {
        gain_x: f32,
        gain_y: f32,
        gain_i: f32,
        gain_o: f32,
        gain_x_s: Smoother,
        gain_y_s: Smoother,
        gain_i_s: Smoother,
        gain_o_s: Smoother,
        audio: Vec<f32>,
        index: usize,
        smooth: f32,
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
                "desc": "Input tap amount. If this is 0, no sound enters the delay.",
                "default": "1.0",
            }],
        },
        "gain_y": {
            "args": [{
                "name": "gain_y",
                "optional": true,
                "desc": "Output tap amount (feedback). How much of the delay's output should be fed back in to the delay.",
                "default": "0.0",
            }],
        },
        "gain_i": {
            "args": [{
                "name": "gain_i",
                "optional": true,
                "desc": "Monitor amount. How much of the original sound should remain.",
                "default": "0.0",
            }],
        },
        "gain_o": {
            "args": [{
                "name": "gain_o",
                "optional": true,
                "desc": "Output amount. How much of the delay's output should be added to the original sound.",
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
        self.gain_x_s.smooth(self.gain_x, self.smooth);
        self.gain_y_s.smooth(self.gain_y, self.smooth);
        self.gain_i_s.smooth(self.gain_i, self.smooth);
        self.gain_o_s.smooth(self.gain_o, self.smooth);
        for i in 0..self.run_size {
            let x = audio[i];
            let y = self.audio[self.index];
            audio[i] = x * self.gain_i_s.b + y * self.gain_o_s.b;
            self.audio[self.index] = x * self.gain_x_s.b + y * self.gain_y_s.b;
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
            if self.index >= self.audio.len() {
                self.index = 0;
            }
        }
        Ok(Some(json!(self.audio.len())))
    }
}
