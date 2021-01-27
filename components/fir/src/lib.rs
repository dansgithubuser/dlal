use dlal_component_base::{component, json, serde_json, Body, CmdResult};

use rustfft::{num_complex::Complex, FFTplanner};

component!(
    {"in": [], "out": ["audio"]},
    ["run_size", "uni", "check_audio"],
    {
        ir: Vec<f32>,
        state: Vec<f32>,
        index: usize,
        smooth: f32,
        ir_dst: Vec<f32>,
    },
    {
        "ir": {
            "args": [
                {
                    "name": "ir",
                    "type": "array",
                    "element": "float",
                },
                {
                    "name": "smooth",
                    "default": 0,
                    "range": "[0, 1]",
                },
            ],
        },
        "bandpass": {
            "args": [
                {
                    "name": "center",
                    "range": "[0, 1]",
                },
                {
                    "name": "width",
                    "optional": true,
                    "default": 2.0,
                },
                {
                    "name": "size",
                    "optional": true,
                    "default": "128",
                },
                {
                    "name": "amplitude",
                    "optional": true,
                    "default": "1",
                },
            ],
        },
        "gain": {
            "args": [
                {
                    "name": "factor",
                    "default": 1,
                    "range": "[0, inf)",
                },
                {
                    "name": "smooth",
                    "default": 0,
                    "range": "[0, 1]",
                },
            ],
        },
    },
);

impl ComponentTrait for Component {
    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({
            "ir": self.ir,
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = body.arg::<serde_json::Value>(0)?;
        self.set_ir(j.at("ir")?);
        Ok(None)
    }

    fn run(&mut self) {
        if self.ir.is_empty() {
            return;
        }
        if self.smooth != 0.0 {
            for i in 0..self.ir.len() {
                self.ir[i] = self.ir[i] * self.smooth + self.ir_dst[i] * (1.0 - self.smooth);
            }
        }
        if let Some(output) = &self.output {
            for i in output.audio(self.run_size).unwrap() {
                self.state[self.index] = *i;
                *i = 0.0;
                for j in 0..self.ir.len() {
                    *i += self.ir[j] * self.state[(self.index + j) % self.state.len()];
                }
                self.index += self.state.len() - 1;
                self.index %= self.state.len();
            }
        }
    }
}

impl Component {
    fn sync_state(&mut self) {
        self.state.resize(self.ir.len(), 0.0);
        if self.index > self.state.len() {
            self.index = 0;
        }
    }

    fn set_ir(&mut self, ir: Vec<f32>) {
        self.ir = ir;
        self.sync_state();
    }

    fn set_ir_smooth(&mut self, ir: Vec<f32>, smooth: f32) {
        self.smooth = smooth;
        if self.smooth == 0.0  {
            self.set_ir(ir);
        } else {
            self.ir_dst = ir;
            if self.ir.len() != self.ir_dst.len() {
                self.ir.resize(self.ir_dst.len(), 0.0);
                self.sync_state();
            }
        }
    }

    fn ir_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.set_ir_smooth(body.arg(0)?, body.arg(1).unwrap_or(0.0));
        Ok(None)
    }

    fn bandpass_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let center: f32 = body.arg(0)?;
        let width: f32 = match body.arg(1) {
            Ok(width) => width,
            Err(_) => 2.0,
        };
        let size: usize = match body.arg(2) {
            Ok(size) => size,
            Err(_) => 128,
        };
        let amplitude: f32 = match body.arg(3) {
            Ok(amplitude) => amplitude,
            Err(_) => 1.0,
        };
        let mut fr = (0..(size + 1))
            .map(|i| {
                Complex::new(
                    amplitude
                        * (1.0 - ((i as f32 - center * size as f32) / width).powf(2.0)).max(0.0),
                    0.0,
                )
            })
            .collect::<Vec<Complex<f32>>>();
        for i in 1..size {
            fr.push(fr[size - i]);
        }
        let mut planner = FFTplanner::new(true);
        let fft = planner.plan_fft(2 * size);
        let mut ir = vec![Complex::<f32>::new(0.0, 0.0); 2 * size];
        fft.process(&mut fr, &mut ir);
        self.set_ir(ir.iter().map(|i| i.re).collect());
        Ok(None)
    }

    fn gain_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let factor = body.arg(0).unwrap_or(1.0);
        let smooth = body.arg(1).unwrap_or(0.0);
        self.set_ir_smooth(self.ir.iter().map(|i| i * factor).collect(), smooth);
        Ok(None)
    }
}
