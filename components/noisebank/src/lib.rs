use dlal_component_base::{component, err, json_to_ptr, serde_json, Body, CmdResult};

use rand::random;
use rustfft::{num_complex::Complex, FftPlanner};

use std::f32::consts::PI;

fn smooth(x: &mut f32, xf: f32, smooth: f32) {
    *x = *x * smooth + xf * (1.0 - smooth);
}

struct NoiseBin {
    w_i: f32,
    w_f: f32,
    audio: Vec<f32>,
    index: usize,
    vol: f32,
}

impl NoiseBin {
    fn new(w_i: f32, w_f: f32) -> Self {
        Self {
            w_i,
            w_f,
            audio: vec![],
            index: 0,
            vol: 0.0,
        }
    }

    fn init(&mut self) {
        let size = 30000 + 2 * (random::<usize>() % 5000);
        let w_per_bin = 1.0 / size as f32;
        let c0 = Complex { re: 0.0, im: 0.0 };
        let mut planner = FftPlanner::new();
        let fft = planner.plan_fft_inverse(size);
        let mut buffer = vec![c0];
        for i in 1..size / 2 + 1 {
            let w = i as f32 * w_per_bin;
            if self.w_i <= w && w < self.w_f {
                buffer.push(Complex::from_polar(
                    1.0,
                    2.0 * PI * random::<f32>(),
                ));
            } else {
                buffer.push(c0);
            }
        }
        for i in size / 2 + 1..size {
            buffer.push(buffer[size - i].conj());
        }
        fft.process(&mut buffer);
        let m = buffer.iter().map(|i| i.re.abs()).reduce(f32::max).unwrap();
        self.audio = buffer.iter().map(|i| i.re / m).collect();
    }

    fn run(&mut self) -> f32 {
        self.index += 1;
        self.index %= self.audio.len();
        self.vol * self.audio[self.index]
    }
}

component!(
    {"in": ["cmd"], "out": ["audio"]},
    [
        "run_size",
        "sample_rate",
        "uni",
        "check_audio",
        {"name": "field_helpers", "fields": ["smooth"], "kinds": ["rw", "json"]},
    ],
    {
        joined: bool,
        bins: Vec<NoiseBin>,
        spectrum_e: Vec<f32>,
        spectrum_f: Vec<f32>,
        smooth: f32,
    },
    {
        "configure_bins": {
            "args": [
                {"name": "mode", "options": ["linear", "custom"]},
                {"name": "n_bins", "type": "usize", "desc": "for linear mode"},
                {"name": "bin_centers", "type": "[w, ...]", "desc": "for custom mode"},
            ],
        },
        "spectrum": {
            "args": [{
                "name": "spectrum",
                "type": "array[n_bins]",
                "element": "float",
            }],
        },
        "stft": {
            "args": [{
                "name": "stft",
                "kind": "norm",
             }],
        },
        "piecewise": {
            "args": [
                {
                    "name": "frequencies",
                    "type": "array",
                    "element": "float",
                },
                {
                    "name": "amplitudes",
                    "type": "array",
                    "element": "float",
                },
            ],
        },
    },
);

impl ComponentTrait for Component {
    fn join(&mut self, _body: serde_json::Value) -> CmdResult {
        for bin in &mut self.bins {
            bin.init();
        }
        self.joined = true;
        Ok(None)
    }

    fn run(&mut self) {
        let output = match self.output.as_ref() {
            Some(v) => v,
            None => return,
        };
        for i in output.audio(self.run_size).unwrap().iter_mut() {
            if self.smooth != 0.0 {
                for i in 0..self.bins.len() {
                    smooth(&mut self.spectrum_e[i], self.spectrum_f[i], self.smooth);
                    smooth(&mut self.bins[i].vol, self.spectrum_e[i], self.smooth);
                }
            }
            for bin in &mut self.bins {
                *i += bin.run();
            }
        }
    }
}

impl Component {
    fn configure_bins_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if self.joined {
            return Err(err!("must configure bins before joining").into());
        }
        let mode = body.kwarg::<String>("mode")?;
        match mode.as_str() {
            "linear" => {
                let n_bins = body.kwarg::<usize>("n_bins")?;
                let w_per_bin = 1.0 / (2.0 * n_bins as f32);
                self.bins = (0..n_bins)
                    .map(|i| NoiseBin::new(
                        (i + 0) as f32 * w_per_bin,
                        (i + 1) as f32 * w_per_bin,
                    ))
                    .collect();
            }
            "custom" => {
                let bin_centers = body.kwarg::<Vec<f32>>("bin_centers")?;
                if bin_centers.len() < 2 {
                    return Err(err!("too few bin centers").into());
                }
                self.bins.clear();
                for i in 0..bin_centers.len() {
                    let w_center = bin_centers[i];
                    let w_edge = if i > 0 {
                        bin_centers[i - 1]
                    } else {
                        bin_centers[1]
                    };
                    let w_size = (w_center - w_edge).abs();
                    self.bins.push(NoiseBin::new(
                        w_center - w_size,
                        w_center + w_size,
                    ));
                }
            }
            x => return Err(err!("unknown mode {}", x).into()),
        }
        self.spectrum_e = vec![0.0; self.bins.len()];
        self.spectrum_f = vec![0.0; self.bins.len()];
        Ok(None)
    }

    fn spectrum_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let spectrum = body.arg::<Vec<f32>>(0)?;
        if spectrum.len() != self.bins.len() {
            return Err(err!("spectrum must be length {}", self.bins.len()).into());
        }
        if self.smooth != 0.0 {
            self.spectrum_f = spectrum;
            self.spectrum_e.resize(self.bins.len(), 0.0);
        } else {
            for i in 0..self.bins.len() {
                self.bins[i].vol = spectrum[i];
            }
        }
        Ok(None)
    }

    fn stft_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let data = json_to_ptr!(body.arg::<serde_json::Value>(0)?, *const f32);
        let len = body.arg(1)?;
        let stft = unsafe { std::slice::from_raw_parts(data, len) };
        for bin in &mut self.bins {
            bin.vol = 0.0;
        }
        let mut i = 0;
        'stft: for j in 0..(len / 2 + 1) {
            let w = j as f32 / len as f32;
            while self.bins[i].w_f <= w {
                i += 1;
                if i >= self.bins.len() {
                    break 'stft;
                }
            }
            self.bins[i].vol += stft[j];
        }
        Ok(None)
    }

    fn piecewise_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let freqs = body.arg::<Vec<f32>>(0)?;
        let amps = body.arg::<Vec<f32>>(1)?;
        let mut spectrum = vec![0.0; self.bins.len()];
        let mut j = 0;
        for (i, v) in spectrum.iter_mut().enumerate() {
            let f = (self.bins[i].w_i + self.bins[i].w_f) / 2.0 * self.sample_rate as f32;
            while j + 1 < freqs.len() && f > freqs[j + 1] {
                j += 1;
            }
            if j + 1 >= freqs.len() {
                break;
            }
            let t = (f - freqs[j]) / (freqs[j + 1] - freqs[j]);
            *v = amps[j] * (1.0 - t) + amps[j + 1] * t;
        }
        if self.smooth != 0.0 {
            self.spectrum_f = spectrum;
            self.spectrum_e.resize(self.bins.len(), 0.0);
        } else {
            for i in 0..self.bins.len() {
                self.bins[i].vol = spectrum[i];
            }
        }
        Ok(None)
    }
}
