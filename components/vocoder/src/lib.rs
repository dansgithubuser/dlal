use dlal_component_base::{component, serde_json, CmdResult};

use num_complex::Complex64;

struct Band {
    a1: f64,
    a2: f64,
    b0: f64,
    b1: f64,
    sustain: f32,
    d_m: Vec<f64>,
    d_c: Vec<f64>,
    amp: f32,
}

impl Default for Band {
    fn default() -> Self {
        Self {
            a1: 0.0,
            a2: 0.0,
            b0: 1.0,
            b1: 0.0,
            sustain: 0.99,
            d_m: vec![0.0; 2],
            d_c: vec![0.0; 2],
            amp: 0.0,
        }
    }
}

impl Band {
    fn new() -> Self {
        Self::default()
    }

    fn narrow(mut self, w: f64) -> Self {
        let width = 0.02;
        let p = Complex64::from_polar(1.0 - width, w);
        let z_w = Complex64::from_polar(1.0, w);
        self.b0 = ((z_w - p) * (z_w - p.conj())).norm();
        self.b1 = 0.0;
        self.a1 = -(p + p.conj()).re;
        self.a2 = (p * p.conj()).re;
        self
    }

    fn high_pass(mut self, w: f64) -> Self {
        let alpha = 1.0 / (w + 1.0);
        self.a1 = -alpha;
        self.a2 = 0.0;
        self.b0 = alpha;
        self.b1 = -alpha;
        self
    }

    fn analyze(&mut self, x: &Vec<f32>) {
        for i in x {
            self.amp *= self.sustain;
            self.amp = f32::max(self.filter_modulator(*i).abs(), self.amp);
        }
    }

    fn filter_modulator(&mut self, x: f32) -> f32 {
        let x = x as f64;
        let y = self.b0 * x + self.d_m[0];
        self.d_m[0] = self.b1 * x - self.a1 * y + self.d_m[1];
        self.d_m[1] = -self.a2 * y;
        y as f32
    }

    fn filter_carrier(&mut self, x: f32) -> f32 {
        let x = x as f64;
        let y = self.b0 * x + self.d_c[0];
        self.d_c[0] = self.b1 * x - self.a1 * y + self.d_c[1];
        self.d_c[1] = -self.a2 * y;
        y as f32 * self.amp
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
        let tau = 2.0 * std::f64::consts::PI;
        let s = self.sample_rate as f64;
        let t_o = self.tone_order as f64;
        let t_c = self.tone_cutoff as f64;
        let n_c = self.noise_cutoff as f64;
        self.bands = (0..self.tone_order)
            .map(|i| {
                let w_full = tau * (i as f64 + 1.0) / t_o;
                Band::new().narrow(w_full * t_c / s)
            })
            .collect();
        self.bands.push(Band::new().high_pass(tau * n_c / s));
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
            println!("{:?}", self.bands.iter().map(|i| (i.amp * 100.0) as i32).collect::<Vec<_>>());
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
