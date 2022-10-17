use dlal_component_base::{component, err, json_to_ptr, serde_json, Body, CmdResult};

use rand::random;
use rustfft::{num_complex::Complex, FftPlanner};

use std::f32::consts::PI;

fn smooth(x: &mut f32, xf: f32, smooth: f32) {
    *x = *x * smooth + xf * (1.0 - smooth);
}

const BINS: usize = 64;

struct NoiseBin {
    audio: Vec<f32>,
    index: usize,
    vol: f32,
}

impl NoiseBin {
    fn new() -> Self {
        Self {
            audio: vec![],
            index: 0,
            vol: 0.0,
        }
    }

    fn init(&mut self, freq_i: f32, freq_f: f32, sample_rate: u32) {
        let size = 30000 + 2 * (random::<usize>() % 5000);
        let freq_per_bin = sample_rate as f32 / size as f32;
        let c0 = Complex { re: 0.0, im: 0.0 };
        let mut planner = FftPlanner::new();
        let fft = planner.plan_fft_inverse(size);
        let mut buffer = vec![c0];
        for i in 1..size / 2 + 1 {
            let freq = i as f32 * freq_per_bin;
            if freq_i <= freq && freq < freq_f {
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

    fn run(&mut self, audio: &mut [f32]) {
        for i in audio.iter_mut() {
            *i += self.vol * self.audio[self.index];
            self.index += 1;
            self.index %= self.audio.len();
        }
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
        bins: Vec<NoiseBin>,
        spectrum_e: Vec<f32>,
        spectrum_f: Vec<f32>,
        smooth: f32,
    },
    {
        "spectrum": {
            "args": [{
                "name": "spectrum",
                "type": "array[64]",
                "element": "float",
            }],
        },
        "stft": {
            "args": [{
                "name": "stft",
                "kind": "norm",
             }],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.bins = (0..BINS).map(|_| NoiseBin::new()).collect();
        self.spectrum_e = vec![0.0; BINS];
        self.spectrum_f = vec![0.0; BINS];
    }

    fn join(&mut self, _body: serde_json::Value) -> CmdResult {
        let freq_per_bin = self.sample_rate as f32 / (2.0 * BINS as f32);
        for i in 0..BINS {
            self.bins[i].init(
                (i + 0) as f32 * freq_per_bin,
                (i + 1) as f32 * freq_per_bin,
                self.sample_rate,
            );
        }
        Ok(None)
    }

    fn run(&mut self) {
        if self.smooth != 0.0 {
            for i in 0..BINS {
                smooth(&mut self.spectrum_e[i], self.spectrum_f[i], self.smooth);
                smooth(&mut self.bins[i].vol, self.spectrum_e[i], self.smooth);
            }
        }
        let output = match self.output.as_ref() {
            Some(v) => v,
            None => return,
        };
        let audio = output.audio(self.run_size).unwrap();
        for bin in &mut self.bins {
            bin.run(audio);
        }
    }
}

impl Component {
    fn spectrum_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let spectrum = body.arg::<Vec<f32>>(0)?;
        if spectrum.len() != BINS {
            return Err(err!("spectrum must be length 64").into());
        }
        if self.smooth != 0.0 {
            self.spectrum_f = spectrum;
            self.spectrum_e.resize(BINS, 0.0);
        } else {
            for i in 0..BINS {
                self.bins[i].vol = spectrum[i];
            }
        }
        Ok(None)
    }

    fn stft_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let data = json_to_ptr!(body.arg::<serde_json::Value>(0)?, *const f32);
        let len = body.arg(1)?;
        let stft = unsafe { std::slice::from_raw_parts(data, len) };
        for i in 0..self.bins.len() {
            self.bins[i].vol = stft[i * (len / 2 + 1) / self.bins.len()];
        }
        Ok(None)
    }
}
