use dlal_component_base::{command, gen_component, join, json, uni, View, Body, Error, Arg, serde_json};

use num_complex::Complex64;
use polynomials::{Polynomial, poly};

use std::collections::HashMap;

fn hysteresis(a: &mut f64, b: f64, smooth: f64) {
    *a = *a * smooth + b * (1.0 - smooth);
}

fn hysteresis_vec(a: &mut Vec<Complex64>, b: &Vec<Complex64>, smooth: f64) {
    for i in 0..a.len() {
        if i >= b.len() {
            break;
        }
        a[i] = a[i] * smooth + b[i] * (1.0 - smooth);
    }
}

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    a: Vec<f64>,
    b: Vec<f64>,
    d: Vec<f64>,
    poles: Vec<Complex64>,
    zeros: Vec<Complex64>,
    gain: f64,
    smooth: Option<f64>,
    poles_dst: Vec<Complex64>,
    zeros_dst: Vec<Complex64>,
    gain_dst: f64,
    output: Option<View>,
}

impl Specifics {
    fn set_a(&mut self, a: Vec<f64>) {
        self.a = a;
        let b_len = self.b.iter().position(|&i| i == 0.0).unwrap_or(self.b.len());
        if self.a.len() > b_len {
            self.d.resize(self.a.len(), 0.0);
            self.b.resize(self.a.len(), 0.0);
        } else {
            self.a.resize(self.d.len(), 0.0);
        }
    }

    fn set_b(&mut self, b: Vec<f64>) {
        self.b = b;
        let a_len = self.a.iter().position(|&i| i == 0.0).unwrap_or(self.a.len());
        if self.b.len() > a_len {
            self.d.resize(self.b.len(), 0.0);
            self.a.resize(self.b.len(), 0.0);
        } else {
            self.b.resize(self.d.len(), 0.0);
        }
    }

    fn pole_zero(&mut self) {
        /*
        The polynomials package only works with positive exponents, but we want negative ones. So let's define z' as 1/z.

        The equation we want to evaluate:
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
}

gen_component!(Specifics, {"in": [], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            a: vec![1.0],
            b: vec![1.0],
            ..Default::default()
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                soul.samples_per_evaluation = body.kwarg("samples_per_evaluation")?;
                Ok(None)
            },
            ["samples_per_evaluation"],
        );
        uni!(connect commands, true);
        command!(
            commands,
            "a",
            |soul, body| {
                if let Ok(a) = body.arg::<Vec<_>>(0) {
                    let a = a.vec()?;
                    if a.len() == 0 {
                        Error::err("expecting an array with at least one element")?;
                    }
                    soul.set_a(a);
                }
                soul.smooth = None;
                Ok(Some(json!(soul.a)))
            },
            { "args": ["a"] },
        );
        command!(
            commands,
            "b",
            |soul, body| {
                if let Ok(b) = body.arg::<Vec<_>>(0) {
                    soul.set_b(b.vec()?);
                }
                soul.smooth = None;
                Ok(Some(json!(soul.b)))
            },
            { "args": ["b"] },
        );
        command!(
            commands,
            "pole_zero",
            |soul, body| {
                // poles
                let poles: Vec<Complex64> = body.arg::<Vec<_>>(0)?
                    .vec_map(|i| {
                        Ok(Complex64::new(i.at("re")?, i.at("im")?))
                    })?;
                // zeros
                let zeros: Vec<Complex64> = body.arg::<Vec<_>>(1)?
                    .vec_map(|i| {
                        Ok(Complex64::new(i.at("re")?, i.at("im")?))
                    })?;
                // gain
                let gain = body.arg(2)?;
                // smooth
                let smooth = body.kwarg("smooth").unwrap_or(0.0);
                if smooth != 0.0 {
                    soul.smooth = Some(smooth);
                    soul.poles_dst = poles;
                    soul.zeros_dst = zeros;
                    soul.gain_dst = gain;
                } else {
                    soul.smooth = None;
                    soul.poles = poles;
                    soul.zeros = zeros;
                    soul.gain = gain;
                    soul.pole_zero();
                }
                // finish
                Ok(None)
            },
            {
                "args": ["poles", "zeros", "gain"],
                "kwargs": ["smooth"],
            },
        );
        command!(
            commands,
            "pole_zero_get",
            |soul, _body| {
                Ok(Some(json!({
                    "poles": soul.poles.iter().map(|i| {
                        let mut ret = HashMap::new();
                        ret.insert("re", i.re);
                        ret.insert("im", i.im);
                        ret
                    }).collect::<Vec<_>>(),
                    "zeros": soul.zeros.iter().map(|i| {
                        let mut ret = HashMap::new();
                        ret.insert("re", i.re);
                        ret.insert("im", i.im);
                        ret
                    }).collect::<Vec<_>>(),
                    "gain": soul.gain,
                })))
            },
            { "args": ["b"] },
        );
        command!(
            commands,
            "single_pole_bandpass",
            |soul, body| {
                let w = body.arg(0)?;
                let width = body.arg::<f64>(1)?;
                let peak = body.arg(2).unwrap_or(1.0);
                let smooth = body.arg(3).unwrap_or(0.0);
                /* How would we get a peak of 1?
                H(z) = gain / ((z - p)*(z - p.conjugate()))
                We can control gain
                Max response is at z_w = cmath.rect(1, w)
                gain = abs((z_w - p)*(z_w - p.conjugate())) */
                let p = Complex64::from_polar(1.0 - width, w);
                let z_w = Complex64::from_polar(1.0, w);
                let gain = peak * ((z_w - p) * (z_w - p.conj())).norm();
                if smooth != 0.0 {
                    soul.smooth = Some(smooth);
                    soul.poles_dst = vec![p, p.conj()];
                    soul.zeros_dst = vec![];
                    soul.gain_dst = gain;
                } else {
                    soul.smooth = None;
                    soul.poles = vec![p, p.conj()];
                    soul.zeros = vec![];
                    soul.gain = gain;
                    soul.pole_zero();
                }
                Ok(None)
            },
            {
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
                ],
            },
        );
        command!(
            commands,
            "wash",
            |soul, _body| {
                let result = Ok(Some(json!(soul.d)));
                for i in soul.d.iter_mut() {
                    *i = 0.0;
                }
                result
            },
            { "args": ["b"] },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| {
                Ok(Some(json!({
                    "a": soul.a,
                    "b": soul.b,
                })))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                let j = body.arg::<serde_json::Value>(0)?;
                soul.set_a(j.at::<Vec<_>>("a")?.vec()?);
                soul.set_b(j.at::<Vec<_>>("b")?.vec()?);
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        if let Some(smooth) = self.smooth {
            hysteresis_vec(&mut self.poles, &self.poles_dst, smooth);
            hysteresis_vec(&mut self.zeros, &self.zeros_dst, smooth);
            hysteresis(&mut self.gain, self.gain_dst, smooth);
            self.pole_zero();
        }
        let output = match &self.output {
            Some(output) => output,
            None => return,
        };
        if self.a.is_empty() || self.b.is_empty() || self.d.is_empty() {
            return;
        }
        for i in output.audio(self.samples_per_evaluation).unwrap() {
            let y = (self.b[0] * (*i as f64) + self.d[0]) / self.a[0];
            for j in 1..self.d.len() {
                self.d[j - 1] = self.b[j] * (*i as f64) - self.a[j] * y + self.d[j];
            }
            *i = y as f32;
        }
    }
}
