use dlal_component_base::{component, err, json, serde_json, Body, CmdResult, View};

use rustfft::{num_complex::Complex, Fft, FftPlanner};

use std::f32::consts::PI;
use std::sync::Arc;

component!(
    {"in": ["audio"], "out": ["cmd"]},
    [
        "audio",
        {
            "name": "connect_info",
            "args": "view",
            "kwargs": {
                "name": "kind",
                "default": "norm",
                "options": ["norm"]
            }
        },
        {"name": "field_helpers", "fields": ["last_error"], "kinds": ["r"]},
        {"name": "field_helpers", "fields": ["smooth"], "kinds": ["rw", "json"]},
    ],
    {
        outputs_norm: Vec<View>,
        input: Vec<f32>,
        fft: Option<Arc<Fft<f32>>>,
        buffer: Vec<Complex<f32>>,
        scratch: Vec<Complex<f32>>,
        output_norm: Vec<f32>,
        smooth: f32,
        last_error: String,
    },
    {
        "window_size": {"args": ["size"]},
        "spectrum": {"args": []},
        "cepstrum": {"args": []},
    },
);

impl Component {
    fn set_window_size(&mut self, size: usize) {
        self.input.resize(size, 0.0);
        self.fft = Some(FftPlanner::new().plan_fft_forward(size));
        self.buffer.resize(size, Complex { re: 0.0, im: 0.0 });
        self.scratch.resize(
            self.fft.as_ref().unwrap().get_inplace_scratch_len(),
            Complex { re: 0.0, im: 0.0 },
        );
        self.output_norm.resize(size, 0.0);
    }
}

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.set_window_size(64);
        self.smooth = 0.5;
    }

    fn run(&mut self) {
        let window_size = self.input.len();
        for i in 0..window_size - self.run_size {
            self.input[i] = self.input[i + self.run_size];
        }
        for i in 0..self.run_size {
            self.input[window_size - self.run_size + i] = self.audio[i];
        }
        for i in 0..window_size {
            let w = 1.0 - (2.0 * PI * i as f32 / (window_size as f32 - 1.0)).cos();
            self.buffer[i] = Complex {
                re: self.input[i] * w,
                im: 0.0,
            };
        }
        self.fft
            .as_ref()
            .unwrap()
            .process_with_scratch(&mut self.buffer, &mut self.scratch);
        if !self.outputs_norm.is_empty() {
            for i in 0..window_size {
                self.output_norm[i] *= self.smooth;
                self.output_norm[i] +=
                    (1.0 - self.smooth) * (self.buffer[i].norm() / window_size as f32);
            }
        }
        for output in &self.outputs_norm {
            let body = json!({
                "name": "stft",
                "args": [
                    (self.output_norm.as_ptr() as usize).to_string(),
                    window_size,
                ],
            });
            if let Some(result) = output.command(&body) {
                if let Some(error) = result.get("error") {
                    self.last_error = error.as_str().unwrap_or(&error.to_string()).into();
                }
            }
        }
        for i in &mut self.audio {
            *i = 0.0;
        }
    }

    fn connect(&mut self, body: serde_json::Value) -> CmdResult {
        let connectee = View::new(&body.at("args")?)?;
        match body
            .kwarg::<String>("kind")
            .unwrap_or("norm".into())
            .as_str()
        {
            "norm" => {
                self.outputs_norm.push(connectee);
            }
            _ => Err(err!("invalid kind"))?,
        };
        Ok(None)
    }

    fn disconnect(&mut self, body: serde_json::Value) -> CmdResult {
        let connectee = View::new(&body.at("args")?)?;
        if let Some(i) = self.outputs_norm.iter().position(|i| i == &connectee) {
            self.outputs_norm.remove(i);
        }
        Ok(None)
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(field_helper_to_json!(self, {
            "window_size": self.buffer.len(),
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = field_helper_from_json!(self, body);
        self.set_window_size(j.at("window_size")?);
        Ok(None)
    }
}

impl Component {
    fn window_size_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.set_window_size(body.arg(0)?);
        Ok(None)
    }

    fn spectrum_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        let window_size = self.input.len();
        Ok(Some(json!(
            self.buffer[..window_size / 2 + 1]
                .iter()
                .map(|i| i.norm() / window_size as f32)
                .collect::<Vec<_>>()
        )))
    }

    fn cepstrum_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        let window_size = self.input.len();
        let mut buffer = self.buffer
            .iter()
            .map(|i| Complex {
                re: (i.norm() / window_size as f32).max(1e-20).ln(),
                im: 0.0,
            })
            .collect::<Vec<_>>();
        self.fft
            .as_ref()
            .unwrap()
            .process_with_scratch(&mut buffer, &mut self.scratch);
        Ok(Some(json!(
            buffer[..window_size / 2 + 1]
                .iter()
                .map(|i| i.norm())
                .collect::<Vec<_>>()
        )))
    }
}
