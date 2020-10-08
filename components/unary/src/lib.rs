use dlal_component_base::{command, gen_component, join, json, multi, View, Body, serde_json};

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
                soul.samples_per_evaluation = body.kwarg("samples_per_evaluation")?;
                Ok(None)
            },
            ["samples_per_evaluation"],
        );
        multi!(connect commands, true);
        command!(
            commands,
            "mode",
            |soul, body| {
                if let Ok(v) = body.arg(0) {
                    soul.mode = v;
                }
                Ok(Some(json!(soul.mode)))
            },
            {
                "args": [{
                    "name": "mode",
                    "optional": true,
                    "choices": ["exp2", "sqrt"],
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
                let j = body.arg::<serde_json::Value>(0)?;
                soul.mode = j.at("mode")?;
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
                    "sqrt" => {
                        if *i >= 0.0 {
                            i.sqrt()
                        } else {
                            -(-*i).sqrt()
                        }
                    }
                    _ => *i,
                }
            }
        }
    }
}
