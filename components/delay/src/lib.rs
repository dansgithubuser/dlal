use dlal_component_base::{component, json, serde_json, Body, CmdResult};

component!(
    {"in": [], "out": ["audio"]},
    ["run_size", "uni", "check_audio"],
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
        Ok(Some(json!({
            "size": self.audio.len(),
            "gain_x": self.gain_x,
            "gain_y": self.gain_y,
            "gain_i": self.gain_i,
            "gain_o": self.gain_o,
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = body.arg::<serde_json::Value>(0)?;
        self.audio.resize(j.at("size")?, 0.0);
        self.gain_x = j.at("gain_x")?;
        self.gain_y = j.at("gain_y")?;
        self.gain_i = j.at("gain_i")?;
        self.gain_o = j.at("gain_o")?;
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

    fn gain_x_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.gain_x = v;
        }
        Ok(Some(json!(self.gain_x)))
    }

    fn gain_y_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.gain_y = v;
        }
        Ok(Some(json!(self.gain_y)))
    }

    fn gain_i_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.gain_i = v;
        }
        Ok(Some(json!(self.gain_i)))
    }

    fn gain_o_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.gain_o = v;
        }
        Ok(Some(json!(self.gain_o)))
    }
}
