use dlal_component_base::{command, gen_component, join, json, marg, uni, View};

use std::vec::Vec;

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    a: Vec<f32>,
    b: Vec<f32>,
    x: Vec<f32>,
    y: Vec<f32>,
    i_x: usize,
    i_y: usize,
    output: Option<View>,
}

impl Specifics {
    fn set_a(&mut self, a: Vec<f32>) {
        self.a = a;
        self.y.resize(self.a.len(), 0.0);
        if self.i_y > self.y.len() {
            self.i_y = 0;
        }
    }

    fn set_b(&mut self, b: Vec<f32>) {
        self.b = b;
        self.x.resize(self.b.len(), 0.0);
        if self.i_x > self.x.len() {
            self.i_x = 0;
        }
    }
}

gen_component!(Specifics, {"in": [], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
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
                soul.set_a(marg!(json_f32s marg!(arg &body, 0)?)?);
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
            if !self.x.is_empty() {
                self.x[self.i_x] = *i;
            }
            *i = 0.0;
            for j in 0..self.a.len() {
                *i -= self.a[j] * self.y[(self.i_y + j) % self.y.len()];
            }
            for j in 0..self.b.len() {
                *i += self.b[j] * self.x[(self.i_x + j) % self.x.len()];
            }
            if !self.x.is_empty() {
                self.i_x += self.x.len() - 1;
                self.i_x %= self.x.len();
            }
            if !self.y.is_empty() {
                self.y[self.i_y] = *i;
                self.i_y += self.y.len() - 1;
                self.i_y %= self.y.len();
            }
        }
    }
}
