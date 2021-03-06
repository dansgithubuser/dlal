use dlal_component_base::{component, serde_json, CmdResult};

use biquad::frequency::ToHertz;
use biquad::Biquad;

struct Band {
    modulator_biquads: Vec<biquad::DirectForm2Transposed<f64>>,
    carrier_biquads: Vec<biquad::DirectForm2Transposed<f64>>,
    sustain: f32,
    amp: f32,
}

impl Default for Band {
    fn default() -> Self {
        Self {
            modulator_biquads: vec![],
            carrier_biquads: vec![],
            sustain: 0.99,
            amp: 0.0,
        }
    }
}

impl Band {
    fn new() -> Self {
        Self::default()
    }

    fn narrow(mut self, f: f64, q: f64, sample_rate: f64) -> Self {
        let bq = biquad::DirectForm2Transposed::<f64>::new(
            biquad::Coefficients::<f64>::from_params(
                biquad::Type::BandPass,
                sample_rate.hz(),
                f.hz(),
                q,
            )
            .unwrap(),
        );
        self.modulator_biquads.push(bq.clone());
        self.carrier_biquads.push(bq.clone());
        self
    }

    fn high_pass(mut self, f: f64, sample_rate: f64) -> Self {
        let bq = biquad::DirectForm2Transposed::<f64>::new(
            biquad::Coefficients::<f64>::from_params(
                biquad::Type::HighPass,
                sample_rate.hz(),
                f.hz(),
                biquad::Q_BUTTERWORTH_F64,
            )
            .unwrap(),
        );
        self.modulator_biquads.push(bq.clone());
        self.carrier_biquads.push(bq.clone());
        self
    }

    fn analyze(&mut self, x: &Vec<f32>) {
        for i in x {
            self.amp *= self.sustain;
            self.amp = f32::max(self.filter_modulator(*i).abs(), self.amp);
        }
    }

    fn filter_modulator(&mut self, x: f32) -> f32 {
        let mut x = x as f64;
        for biquad in &mut self.modulator_biquads {
            x = biquad.run(x);
        }
        x as f32
    }

    fn filter_carrier(&mut self, x: f32) -> f32 {
        let mut x = x as f64;
        for biquad in &mut self.carrier_biquads {
            x = biquad.run(x);
        }
        x as f32 * self.amp
    }
}

component!(
    {"in": ["audio"], "out": ["audio"]},
    [
        "run_size",
        "sample_rate",
        "audio",
        "uni",
        "check_audio",
        {
            "name": "field_helpers",
            "fields": [
                "tone_order",
                "tone_cutoff",
                "noise_cutoff"
            ],
            "kinds": ["rw", "json"]
        },
    ],
    {
        tone_order: usize,
        tone_cutoff: u32,
        noise_cutoff: u32,
        bands: Vec<Band>,
    },
    {
        "commit": { "args": [] },
    },
);

impl Component {
    fn commit(&mut self) {
        let s = self.sample_rate as f64;
        let t_o = self.tone_order as f64;
        let t_c = self.tone_cutoff as f64;
        let n_c = self.noise_cutoff as f64;
        self.bands = (0..self.tone_order)
            .map(|i| {
                let i = i as f64;
                Band::new().narrow(
                    (i + 1.0) / t_o * t_c,
                    25.0 + i / 2.0,
                    s,
                )
            })
            .collect();
        self.bands.push(Band::new().high_pass(n_c, s));
    }
}

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.tone_order = 20;
        self.tone_cutoff = 8000;
        self.noise_cutoff = 8000;
    }

    fn join(&mut self, _body: serde_json::Value) -> CmdResult {
        self.commit();
        Ok(None)
    }

    fn run(&mut self) {
        for band in &mut self.bands {
            band.analyze(&self.audio);
        }
        if std::option_env!("DLAL_SNOOP_VOCODER").is_some() {
            println!(
                "{:?}",
                self.bands
                    .iter()
                    .map(|i| (i.amp * 100.0) as i32)
                    .collect::<Vec<_>>(),
            );
        }
        let carrier = match &mut self.output {
            Some(output) => output.audio(self.run_size).unwrap(),
            None => return,
        };
        for i in carrier {
            let mut y = 0.0;
            for band in &mut self.bands {
                y += band.filter_carrier(*i);
            }
            *i = y;
        }
        for i in &mut self.audio {
            *i = 0.0;
        }
    }
}

impl Component {
    fn commit_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        self.commit();
        Ok(None)
    }
}
