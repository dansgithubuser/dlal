use dlal_component_base::{command, err, gen_component, join, json, marg, uni, View};

use num_complex::Complex64;
use polynomials::{Polynomial, poly};

use std::vec::Vec;

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    a: Vec<f64>,
    b: Vec<f64>,
    d: Vec<f64>,
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
                join!(samples_per_evaluation soul, body);
                Ok(None)
            },
            ["samples_per_evaluation"],
        );
        uni!(connect commands, true);
        command!(
            commands,
            "a",
            |soul, body| {
                if let Ok(a) = marg!(arg &body, 0) {
                    let a = marg!(json_f64s a)?;
                    if a.len() == 0 {
                        return err!("expecting an array with at least one element");
                    }
                    soul.set_a(a);
                }
                Ok(Some(json!(soul.a)))
            },
            { "args": ["a"] },
        );
        command!(
            commands,
            "b",
            |soul, body| {
                if let Ok(b) = marg!(arg &body, 0) {
                    soul.set_b(marg!(json_f64s b)?);
                }
                Ok(Some(json!(soul.b)))
            },
            { "args": ["b"] },
        );
        command!(
            commands,
            "pole_zero",
            |soul, body| {
                // poles
                let poles: Vec<Complex64> = marg!(arg &body, 0)?
                    .as_array()
                    .ok_or_else(|| err!(box "expecting an array, but didn't get one"))?
                    .iter()
                    .map::<Result<Complex64, String>, _>(|i| {
                        let re = i
                            .get("re")
                            .unwrap_or(&json!(0))
                            .as_f64()
                            .ok_or_else(|| "real component isn't a number")?;
                        let im = i
                            .get("im")
                            .unwrap_or(&json!(0))
                            .as_f64()
                            .ok_or_else(|| "imaginary component isn't a number")?;
                        Ok(Complex64::new(re, im))
                    })
                    .collect::<Result<_, _>>()?;
                // zeros
                let zeros: Vec<Complex64> = marg!(arg &body, 1)?
                    .as_array()
                    .ok_or_else(|| err!(box "expecting an array, but didn't get one"))?
                    .iter()
                    .map::<Result<Complex64, String>, _>(|i| {
                        let re = i
                            .get("re")
                            .unwrap_or(&json!(0))
                            .as_f64()
                            .ok_or_else(|| "real component isn't a number")?;
                        let im = i
                            .get("im")
                            .unwrap_or(&json!(0))
                            .as_f64()
                            .ok_or_else(|| "imaginary component isn't a number")?;
                        Ok(Complex64::new(re, im))
                    })
                    .collect::<Result<_, _>>()?;
                // gain
                let gain = poly![Complex64::new(marg!(arg_num &body, 2)?, 0.0)];
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
                for zero in zeros {
                    b *= poly![Complex64::new(1.0, 0.0), -zero];
                }
                b *= gain;
                // a
                let mut a = Polynomial::new();
                a.push(Complex64::new(1.0, 0.0));
                for pole in poles {
                    a *= poly![Complex64::new(1.0, 0.0), -pole];
                }
                // finish
                let a: Vec<Complex64> = a.into();
                let b: Vec<Complex64> = b.into();
                soul.set_a(a.iter().map(|i| i.re).collect());
                soul.set_b(b.iter().map(|i| i.re).collect());
                Ok(None)
            },
            { "args": ["poles", "zeros", "gain"] },
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
                let j = marg!(arg &body, 0)?;
                soul.set_a(marg!(json_f64s marg!(json_get j, "a")?)?);
                soul.set_b(marg!(json_f64s marg!(json_get j, "b")?)?);
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        let output = match &self.output {
            Some(output) => output,
            None => return,
        };
        for i in output.audio(self.samples_per_evaluation).unwrap() {
            let y = (self.b[0] * (*i as f64) + self.d[0]) / self.a[0];
            for j in 1..self.d.len() {
                self.d[j - 1] = self.b[j] * (*i as f64) - self.a[j] * y + self.d[j];
            }
            *i = y as f32;
        }
    }
}
