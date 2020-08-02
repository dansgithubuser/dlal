use dlal_component_base::{command, err, gen_component, join, json, marg, uni, View};

use std::vec::Vec;

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    a: Vec<f32>,
    b: Vec<f32>,
    d: Vec<f32>,
    output: Option<View>,
}

impl Specifics {
    fn set_a(&mut self, a: Vec<f32>) {
        self.a = a;
        let b_len = self.b.iter().position(|&i| i == 0.0).unwrap_or(self.b.len());
        if self.a.len() > b_len {
            self.d.resize(self.a.len(), 0.0);
            self.b.resize(self.a.len(), 0.0);
        } else {
            self.a.resize(self.d.len(), 0.0);
        }
    }

    fn set_b(&mut self, b: Vec<f32>) {
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
                let a = marg!(json_f32s marg!(arg &body, 0)?)?;
                if a.len() == 0 {
                    return err!("expecting an array with at least one element");
                }
                soul.set_a(a);
                Ok(None)
            },
            { "args": ["a"] },
        );
        command!(
            commands,
            "b",
            |soul, body| {
                soul.set_b(marg!(json_f32s marg!(arg &body, 0)?)?);
                Ok(None)
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
                soul.set_a(marg!(json_f32s marg!(json_get j, "a")?)?);
                soul.set_b(marg!(json_f32s marg!(json_get j, "b")?)?);
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
            let y = (self.b[0] * *i + self.d[0]) / self.a[0];
            for j in 1..self.d.len() {
                self.d[j - 1] = self.b[j] * *i - self.a[j] * y + self.d[j];
            }
            *i = y;
        }
    }
}
