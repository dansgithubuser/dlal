use dlal_component_base::{component, err, json, serde_json, Body, CmdResult};

use std::{env, f32};

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
        "set": {
            "args": [
                {
                    "name": "angle",
                    "units": "degrees",
                },
                {
                    "name": "distance",
                    "units": "meters",
                    "optional": true,
                },
            ],
            "kwargs": [
                {
                    "name": "flip",
                    "default": "DLAL_PAN_FLIP or false",
                    "desc": "false for right, true for left",
                },
                {
                    "name": "ear_offset",
                    "units": "meters",
                    "default": 0.1,
                },
                {
                    "name": "speed_of_sound",
                    "units": "meters per second",
                    "default": 343,
                },
                {
                    "name": "sample_rate",
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
    fn set_delay(&mut self, delay: f32, sample_rate: u32) {
        self.delay = (delay * sample_rate as f32) as usize + 1;
        self.buf.resize(self.delay, 0.0);
        if self.buf_i >= self.delay {
            self.buf_i = 0;
        }
    }

    fn delay_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let sample_rate = if self.sample_rate != 0 {
            self.sample_rate
        } else {
            body.kwarg("sample_rate")?
        };
        match body.arg::<f32>(0) {
            Ok(v) => {
                self.set_delay(v, sample_rate);
            }
            e => if body.has_arg(0) {
                e?;
            }
        }
        Ok(Some(json!(self.delay as f32 / self.sample_rate as f32)))
    }

    fn set_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let mut angle: f32 = body.arg(0)?;
        let distance: Option<f32> = if body.has_arg(1) {
            Some(body.arg(1)?)
        } else {
            None
        };
        let flip = match body.get("flip") {
            Some(serde_json::Value::Bool(b)) => *b,
            None | Some(serde_json::Value::Null) => match env::var("DLAL_PAN_FLIP") {
                Ok(v) => {
                    let u = v.parse::<u8>()?;
                    u == 1
                }
                _ => false,
            }
            Some(v) => return Err(err!("`flip` should be bool or null but got {}", v).into()),
        };
        let ear_offset: f32 = if body.has_kwarg("ear_offset") {
            body.kwarg("ear_offset")?
        } else {
            0.1
        };
        let speed_of_sound: f32 = if body.has_kwarg("speed_of_sound") {
            body.kwarg("speed_of_sound")?
        } else {
            343.0
        };
        let sample_rate: u32 = if body.has_kwarg("sample_rate") {
            body.kwarg("sample_rate")?
        } else {
            if distance.is_some() && self.sample_rate == 0 {
                return Err(err!("No sample rate, can't calculate delay.").into());
            }
            self.sample_rate
        };
        if flip {
            angle += 180.0;
        }
        angle *= f32::consts::TAU / 360.0;
        let power = (angle.sin() + 1.0) / 2.0;
        let gain = power.sqrt();
        self.gain = gain;
        if let Some(distance) = distance {
            let x_src = distance * angle.sin();
            let y_src = distance * angle.cos();
            let x_ear = ear_offset; // no flipping - angle already flipped if requested
            let y_ear = 0.0;
            let d = ((x_src - x_ear).powf(2.0) + (y_src - y_ear).powf(2.0)).sqrt();
            let delay = d / speed_of_sound;
            self.set_delay(delay, sample_rate);
        }
        Ok(None)
    }
}
