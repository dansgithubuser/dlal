use dlal_component_base::{arg_num, command, gen_component, join, json, uni, View};

use std::vec::Vec;

struct Ring {
    vec: Vec<f32>,
    i: usize,
}

impl Ring {
    fn new(size: usize) -> Self {
        Self {
            vec: vec![0.0; size],
            i: 0,
        }
    }

    fn write(&mut self, value: f32) {
        self.vec[self.i] = value;
        self.i += 1;
        self.i %= self.vec.len();
    }

    fn read(&self) -> f32 {
        self.vec[self.i]
    }
}

pub struct Specifics {
    amount: f32,
    samples_per_evaluation: usize,
    rings: Vec<Ring>,
    output: Option<View>,
}

gen_component!(Specifics);

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        let mut rings = Vec::<Ring>::new();
        rings.push(Ring::new(1921));
        rings.push(Ring::new(5240));
        rings.push(Ring::new(5606));
        rings.push(Ring::new(6152));
        rings.push(Ring::new(6198));
        rings.push(Ring::new(6342));
        rings.push(Ring::new(7965));
        rings.push(Ring::new(12965));
        Self {
            amount: 0.5,
            samples_per_evaluation: 0,
            rings,
            output: None,
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
            "set",
            |soul, body| {
                soul.amount = arg_num(&body, 0)?;
                Ok(None)
            },
            { "args": ["amount"] },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| { Ok(Some(json!(soul.amount.to_string()))) },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                soul.amount = arg_num(&body, 0)?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        if let Some(output) = &self.output {
            for i in output.audio(self.samples_per_evaluation).unwrap() {
                for j in 0..self.rings.len() {
                    *i += self.rings[j].read() * self.amount / (8 + j) as f32;
                }
                for ring in &mut self.rings {
                    ring.write(*i);
                }
            }
        }
    }
}
