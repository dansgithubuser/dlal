use dlal_component_base::{command, gen_component, join, json, marg, multi, View};

use std::vec::Vec;

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    mode: String,
    outputs: Vec<View>,
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
        multi!(connect commands, true);
        command!(
            commands,
            "mode",
            |soul, body| {
                if let Ok(v) = marg!(arg_num &body, 0) {
                    soul.mode = v;
                }
                Ok(Some(json!(soul.mode)))
            },
            {
                "args": [{
                    "name": "mode",
                    "optional": true,
                    "choices": ["exp2"],
                }],
            },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| {
                Ok(Some(json!({
                    "mode": soul.mode,
                })))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                let j = marg!(arg &body, 0)?;
                soul.mode= marg!(json_num marg!(json_get j, "mode")?)?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        for output in &self.outputs {
            for i in output.audio(self.samples_per_evaluation).unwrap() {
                *i = match self.mode.as_str() {
                    "exp2" => i.exp2(),
                    _ => *i,
                }
            }
        }
    }
}
