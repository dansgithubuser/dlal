use dlal_component_base::{command, err, gen_component, join, json, marg, uni, View};

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
