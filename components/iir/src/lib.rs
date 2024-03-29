use dlal_component_base::{component, err, json, serde_json, Arg, Body, CmdResult};

use num_complex::Complex64;
use polynomials::{poly, Polynomial};

use std::collections::HashMap;

fn hysteresis(a: &mut f64, b: f64, smooth: f64) {
    *a = *a * smooth + b * (1.0 - smooth);
}

fn hysteresis_vec(a: &mut Vec<Complex64>, b: &[Complex64], smooth: f64) {
    for i in 0..a.len() {
        if i >= b.len() {
            break;
        }
        let (a_r, a_t) = a[i].to_polar();
        let (b_r, b_t) = b[i].to_polar();
        a[i] = Complex64::from_polar(
            a_r * smooth + b_r * (1.0 - smooth),
            a_t * smooth + b_t * (1.0 - smooth),
        );
    }
}

component!(
    {"in": [], "out": ["audio"]},
    ["run_size", "uni", "check_audio"],
    {
        a: Vec<f64>,
        b: Vec<f64>,
        d: Vec<f64>,
        poles: Vec<Complex64>,
        zeros: Vec<Complex64>,
        gain: f64,
        smooth: f64,
        poles_e: Vec<Complex64>,
        zeros_e: Vec<Complex64>,
        gain_e: f64,
        poles_f: Vec<Complex64>,
        zeros_f: Vec<Complex64>,
        gain_f: f64,
    },
    {
        "a": {"args": ["a"]},
        "b": {"args": ["b"]},
        "pole_zero": {
            "args": ["poles", "zeros", "gain"],
            "kwargs": [
                {
                    "name": "smooth",
                    "default": 0,
                    "range": "[0, 1]",
                },
            ],
        },
        "pole_zero_get": {},
        "pole_pairs_bandpass": {
            "args": [
                {
                    "name": "w",
                    "desc": "angular frequency",
                    "range": "[0, 2*pi)",
                },
                {
                    "name": "width",
                    "range": "(0, 1]",
                },
                {
                    "name": "peak",
                    "default": 1,
                    "range": "[0, 1]",
                },
                {
                    "name": "smooth",
                    "default": 0,
                    "range": "[0, 1]",
                },
                {
                    "name": "pairs",
                    "default": 1,
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
        "wash": {},
    },
);

impl Component {
    fn set_a(&mut self, a: Vec<f64>) {
        self.a = a;
        let b_len = self
            .b
            .iter()
            .position(|&i| i == 0.0)
            .unwrap_or(self.b.len());
        if self.a.len() > b_len {
            self.d.resize(self.a.len(), 0.0);
            self.b.resize(self.a.len(), 0.0);
        } else {
            self.a.resize(self.d.len(), 0.0);
        }
    }

    fn set_b(&mut self, b: Vec<f64>) {
        self.b = b;
        let a_len = self
            .a
            .iter()
            .position(|&i| i == 0.0)
            .unwrap_or(self.a.len());
        if self.b.len() > a_len {
            self.d.resize(self.b.len(), 0.0);
            self.a.resize(self.b.len(), 0.0);
        } else {
            self.b.resize(self.d.len(), 0.0);
        }
    }

    // transforms (self.poles, self.zeros, self.gain) into (self.a, self.b)
    fn pole_zero(&mut self) {
        /*
        The polynomials package only works with positive exponents, but we want negative ones. So let's define z' as 1/z.

        The equation we want to run:
        H(z) = gain * [(1 - q_1 / z)(1 - q_2 / z)...(1 - q_m / z)] / [(1 - p_1 / z)(1 - p_2 / z)...(1 - p_n / z)]
        where q_k is the kth zero and p_k is the kth pole.

        With z' = 1/z:
        H(z) = gain * [(1 - q_1 * z')(1 - q_2 * z')...(1 - q_m * z')] / [(1 - p_1 * z')(1 - p_2 * z')...(1 - p_n * z')]
        */
        // b
        let mut b = Polynomial::new();
        b.push(Complex64::new(1.0, 0.0));
        for zero in &self.zeros {
            b *= poly![Complex64::new(1.0, 0.0), -zero];
        }
        b *= Complex64::new(self.gain, 0.0);
        // a
        let mut a = Polynomial::new();
        a.push(Complex64::new(1.0, 0.0));
        for pole in &self.poles {
            a *= poly![Complex64::new(1.0, 0.0), -pole];
        }
        // set
        let a: Vec<Complex64> = a.into();
        let b: Vec<Complex64> = b.into();
        self.set_a(a.iter().map(|i| i.re).collect());
        self.set_b(b.iter().map(|i| i.re).collect());
    }

    // sets appropriate internal state based on desired poles, zeros, gain, and smoothing
    fn smooth_pole_zero(&mut self, poles: &[Complex64], zeros: &[Complex64], gain: f64, smooth: f64) {
        self.smooth = smooth;
        if smooth != 0.0 {
            self.poles_f = poles.to_vec();
            self.zeros_f = zeros.to_vec();
            self.gain_f = gain;
            let mut do_pole_zero = false;
            if self.poles.len() != poles.len() {
                self.poles = poles.to_vec();
                do_pole_zero = true;
            }
            if self.zeros.len() != zeros.len() {
                self.zeros = zeros.to_vec();
                do_pole_zero = true;
            }
            if do_pole_zero {
                self.pole_zero();
            }
            self.poles_e = self.poles.clone();
            self.zeros_e = self.zeros.clone();
            self.gain_e = self.gain;
        } else {
            self.poles = poles.to_vec();
            self.zeros = zeros.to_vec();
            self.gain = gain;
            self.pole_zero();
        }
    }
}

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.a = vec![1.0];
        self.b = vec![1.0];
        self.d = vec![0.0];
    }

    fn run(&mut self) {
        if self.smooth != 0.0 {
            hysteresis_vec(&mut self.poles_e, &self.poles_f, self.smooth);
            hysteresis_vec(&mut self.zeros_e, &self.zeros_f, self.smooth);
            hysteresis(&mut self.gain_e, self.gain_f, self.smooth);
            hysteresis_vec(&mut self.poles, &self.poles_e, self.smooth);
            hysteresis_vec(&mut self.zeros, &self.zeros_e, self.smooth);
            hysteresis(&mut self.gain, self.gain_e, self.smooth);
            self.pole_zero();
        }
        let output = match &self.output {
            Some(output) => output,
            None => return,
        };
        if self.a.is_empty() || self.b.is_empty() || self.d.is_empty() {
            return;
        }
        for i in output.audio(self.run_size).unwrap() {
            let y = (self.b[0] * (*i as f64) + self.d[0]) / self.a[0];
            for j in 1..self.d.len() {
                self.d[j - 1] = self.b[j] * (*i as f64) - self.a[j] * y + self.d[j];
            }
            *i = y as f32;
        }
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({
            "a": self.a,
            "b": self.b,
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = body.arg::<serde_json::Value>(0)?;
        self.set_a(j.at("a")?);
        self.set_b(j.at("b")?);
        Ok(None)
    }
}

impl Component {
    fn a_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(a) = body.arg::<Vec<_>>(0) {
            if a.is_empty() {
                return Err(err!("expecting an array with at least one element").into());
            }
            self.set_a(a);
        }
        self.smooth = 0.0;
        Ok(Some(json!(self.a)))
    }

    fn b_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(b) = body.arg::<Vec<_>>(0) {
            self.set_b(b);
        }
        self.smooth = 0.0;
        Ok(Some(json!(self.b)))
    }

    fn pole_zero_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        // poles
        let poles: Vec<Complex64> = body
            .arg::<Vec<serde_json::Value>>(0)?
            .vec_map(|i| Ok(Complex64::new(i.at("re")?, i.at("im")?)))?;
        // zeros
        let zeros: Vec<Complex64> = body
            .arg::<Vec<serde_json::Value>>(1)?
            .vec_map(|i| Ok(Complex64::new(i.at("re")?, i.at("im")?)))?;
        // gain
        let gain = body.arg(2)?;
        // smooth
        let smooth = body.kwarg("smooth").unwrap_or(0.0);
        self.smooth_pole_zero(&poles, &zeros, gain, smooth);
        // finish
        Ok(None)
    }

    fn pole_zero_get_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({
            "poles": self.poles.iter().map(|i| {
                let mut ret = HashMap::new();
                ret.insert("re", i.re);
                ret.insert("im", i.im);
                ret
            }).collect::<Vec<_>>(),
            "zeros": self.zeros.iter().map(|i| {
                let mut ret = HashMap::new();
                ret.insert("re", i.re);
                ret.insert("im", i.im);
                ret
            }).collect::<Vec<_>>(),
            "gain": self.gain,
        })))
    }

    fn pole_pairs_bandpass_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let w = body.arg(0)?;
        let width = body.arg::<f64>(1)?;
        let peak = body.arg(2).unwrap_or(1.0);
        let smooth = body.arg(3).unwrap_or(0.0);
        let pairs = body.arg(4).unwrap_or(1);
        let pole = Complex64::from_polar(1.0 - width, w);
        let z = Complex64::from_polar(1.0, w);
        let gain = peak * ((z - pole) * (z - pole.conj())).norm().powf(pairs as f64);
        let mut poles = vec![];
        for _ in 0..pairs {
            poles.push(pole);
            poles.push(pole.conj());
        }
        self.smooth_pole_zero(&poles, &[], gain, smooth);
        Ok(None)
    }

    fn gain_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let factor = body.arg(0).unwrap_or(1.0);
        let smooth = body.arg(1).unwrap_or(0.0);
        self.smooth_pole_zero(&self.poles.clone(), &self.zeros.clone(), self.gain * factor, smooth);
        Ok(None)
    }

    fn wash_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        let result = Ok(Some(json!(self.d)));
        for i in self.d.iter_mut() {
            *i = 0.0;
        }
        result
    }
}
