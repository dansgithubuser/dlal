use dlal_component_base::{arg_num, command, gen_component, join, json, uni, View};

pub struct Specifics {
    amount: f32,
    samples_per_evaluation: usize,
    output: Option<View>,
}

gen_component!(Specifics, {"in": [], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            amount: 1.0,
            samples_per_evaluation: 0,
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
            { "args": ["gain"] },
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
                *i *= self.amount;
            }
        }
    }
}
