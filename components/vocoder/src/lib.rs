use dlal_component_base::{component, json, serde_json, CmdResult};

use biquad::frequency::ToHertz;
use biquad::Biquad;

const RUNS_TO_ZERO: u32 = 1024;

struct Band {
    modulator_biquads: Vec<biquad::DirectForm2Transposed<f64>>,
    carrier_biquads: Vec<biquad::DirectForm2Transposed<f64>>,
    gain: f64,
    attack: f32,
    sustain: f32,
    amp: f32,
}

impl Default for Band {
    fn default() -> Self {
        Self {
            modulator_biquads: vec![],
            carrier_biquads: vec![],
            gain: 1.0,
            attack: 0.01,
            sustain: 0.999,
            amp: 0.0,
        }
    }
}

impl Band {
    fn new() -> Self {
        Self::default()
    }

    fn narrow(mut self, f: f64, q: f64, gain: f64, sample_rate: f64) -> Self {
        let bq = biquad::DirectForm2Transposed::<f64>::new(
            biquad::Coefficients::<f64>::from_params(
                biquad::Type::BandPass,
                sample_rate.hz(),
                f.hz(),
                q,
            )
            .unwrap(),
        );
        for _ in 0..2 {
            self.modulator_biquads.push(bq.clone());
            self.carrier_biquads.push(bq.clone());
        }
        self.gain = gain;
        self
    }

    fn filter_modulator(&mut self, x: f32) {
        let mut x = x as f64;
        for biquad in &mut self.modulator_biquads {
            x = biquad.run(x);
        }
        let x = self.gain * x.abs();
        let x = x as f32;
        if x > self.amp {
            self.amp = self.attack * x + (1.0 - self.attack) * self.amp;
        } else {
            self.amp *= self.sustain;
        }
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
                "order",
                "cutoff"
            ],
            "kinds": ["rw", "json"]
        },
    ],
    {
        order: usize,
        cutoff: u32,
        bands: Vec<Band>,
        zero: u32,
    },
    {
        "commit": { "args": [] },
        "read_band_amps": {},
    },
);

impl Component {
    fn commit(&mut self) {
        let s = self.sample_rate as f64;
        let t_o = self.order as f64;
        let t_c = self.cutoff as f64;
        self.bands = (0..self.order)
            .map(|i| {
                let i = i as f64;
                Band::new().narrow(
                    (i + 1.0) / t_o * t_c,
                    /*
                    q and gains found empirically with the following goals:
                        - intelligible when vocoding
                        - relatively flat response, vocoding a chirp (carrier) with white noise (modulator)
                    note that bands need to get thinner (higher q) as they increase in frequency because we're using linear bands
                    I think this only works with order=40 and cutoff=8000
                    */
                    5.0 + i / 2.0,
                    8.0 / (256.0 + 0.0 * i + 8.0 * i * i + 1.0 * i * i * i),
                    s,
                )
            })
            .collect();
    }
}

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.order = 40;
        self.cutoff = 8000;
        self.zero = RUNS_TO_ZERO;
    }

    fn join(&mut self, _body: serde_json::Value) -> CmdResult {
        self.commit();
        Ok(None)
    }

    fn run(&mut self) {
        // get carrier samples from output
        let carrier = match &mut self.output {
            Some(output) => output.audio(self.run_size).unwrap(),
            None => return,
        };
        // if modulator is zero, and our bands are zero, then all we need to do is zero the carrier
        let zero = match self.audio.iter().max_by(|a, b| a.total_cmp(b)) {
            Some(x) => *x < 1.0e-6,
            None => true,
        };
        if zero {
            if self.zero >= RUNS_TO_ZERO {
                for i in carrier.iter_mut() {
                    *i = 0.0;
                }
                return;
            }
            self.zero += 1;
        } else {
            self.zero = 0;
        }
        // find band amplitudes from modulator and apply to carrier
        for (i_mod, i_car) in self.audio.iter().zip(carrier.iter_mut()) {
            let mut y = 0.0;
            for band in &mut self.bands {
                band.filter_modulator(*i_mod);
                y += band.filter_carrier(*i_car);
            }
            *i_car = y;
        }
        // reset modulator
        for i in &mut self.audio {
            *i = 0.0;
        }
        // snoop
        if std::option_env!("DLAL_SNOOP_VOCODER").is_some() {
            println!(
                "{:?}",
                self.bands
                    .iter()
                    .map(|i| (i.amp * 100.0) as i32)
                    .collect::<Vec<_>>(),
            );
        }
    }
}

impl Component {
    fn commit_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        self.commit();
        Ok(None)
    }

    fn read_band_amps_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!(self.bands
            .iter()
            .map(|band| band.amp)
            .collect::<Vec<_>>()
        )))
    }
}
