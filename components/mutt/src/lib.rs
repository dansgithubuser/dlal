use dlal_component_base::{component, serde_json, Body, CmdResult};

use biquad::Biquad;

use std::iter::zip;

fn hz(f: f32) -> Result<biquad::Hertz<f32>, String> {
    biquad::Hertz::<f32>::from_hz(f).map_err(|e| format!("{:?}", e))
}

component!(
    {"in": ["audio"], "out": ["audio"]},
    [
        "run_size",
        "sample_rate",
        "uni",
        "audio",
        "check_audio",
        {"name": "field_helpers", "fields": ["decay", "e"], "kinds": ["rw", "json"]},
    ],
    {
        value: f32, // follows contour of input
        decay: f32, // how quickly to drop down when input heads to zero
        e: f32, // only when value is greater than this should output signal be multiplied by input signal
        filters: Vec<biquad::DirectForm2Transposed<f32>>, // filter output signal when multiplying
    },
    {
        "filter": {"args": ["n", "a1", "a2", "b0", "b1", "b2"]},
        "filter_lo": {"args": ["n", "freq", "q"]},
        "filter_hi": {"args": ["n", "freq", "q"]},
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.decay = 0.99;
        self.e = 0.01;
    }

    fn run(&mut self) {
        let y = match &self.output {
            Some(output) => output.audio(self.run_size).unwrap(),
            None => return,
        };
        for (i, j) in zip(&self.audio, y) {
            self.value *= self.decay;
            if self.value < *i {
                self.value = *i;
            }
            if self.value > self.e {
                *j *= i / self.value;
                for filter in &mut self.filters {
                    *j = filter.run(*j);
                }
            }
        }
        for i in &mut self.audio {
            *i = 0.0;
        }
    }
}

impl Component {
    fn filter_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.filters.clear();
        self.filters.resize(
            body.arg(0)?,
            biquad::DirectForm2Transposed::<f32>::new(
                biquad::Coefficients::<f32> {
                    a1: body.arg(1)?,
                    a2: body.arg(2)?,
                    b0: body.arg(3)?,
                    b1: body.arg(4)?,
                    b2: body.arg(5)?,
                },
            ),
        );
        Ok(None)
    }

    fn filter_lo_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.filters.clear();
        self.filters.resize(
            body.arg(0)?,
            biquad::DirectForm2Transposed::<f32>::new(
                biquad::Coefficients::<f32>::from_params(
                    biquad::Type::LowPass,
                    hz(self.sample_rate as f32)?,
                    hz(body.arg::<f32>(1)?)?,
                    body.arg::<f32>(2)?,
                ).map_err(|e| format!("{:?}", e))?,
            ),
        );
        Ok(None)
    }

    fn filter_hi_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.filters.clear();
        self.filters.resize(
            body.arg(0)?,
            biquad::DirectForm2Transposed::<f32>::new(
                biquad::Coefficients::<f32>::from_params(
                    biquad::Type::HighPass,
                    hz(self.sample_rate as f32)?,
                    hz(body.arg::<f32>(1)?)?,
                    body.arg::<f32>(2)?,
                ).map_err(|e| format!("{:?}", e))?,
            ),
        );
        Ok(None)
    }
}
