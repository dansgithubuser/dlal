use dlal_component_base::{arg_num, gen_component, json, kwarg_num, uniconnect, View};

pub struct Specifics {
    amount: f32,
    samples_per_evaluation: usize,
    view: Option<View>,
}

gen_component!(Specifics);

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            amount: 1.0,
            samples_per_evaluation: 0,
            view: None,
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        commands.insert(
            "join",
            Command {
                func: Box::new(|soul, body| {
                    soul.samples_per_evaluation = kwarg_num(&body, "samples_per_evaluation")?;
                    Ok(None)
                }),
                info: json!({
                    "kwargs": ["samples_per_evaluation"],
                }),
            },
        );
        uniconnect!(commands, true);
        commands.insert(
            "set",
            Command {
                func: Box::new(|soul, body| {
                    soul.amount = arg_num(&body, 0)?;
                    Ok(None)
                }),
                info: json!({
                    "args": ["gain"],
                }),
            },
        );
    }

    fn evaluate(&mut self) {
        if let Some(view) = &self.view {
            for i in view.audio(self.samples_per_evaluation).unwrap() {
                *i *= self.amount;
            }
        }
    }
}
