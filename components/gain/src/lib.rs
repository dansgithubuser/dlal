use dlal_component_base::{Body, command, gen_component, join, json, uni, View};

pub struct Specifics {
    amount: f32,
    amount_dst: f32,
    smooth: f32,
    samples_per_evaluation: usize,
    output: Option<View>,
}

gen_component!(Specifics, {"in": [], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            amount: 1.0,
            amount_dst: 1.0,
            smooth: 0.0,
            samples_per_evaluation: 0,
            output: None,
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
            "set",
            |soul, body| {
                soul.amount_dst = body.arg(0)?;
                soul.smooth = body.arg(1).unwrap_or(0.0);
                if soul.smooth == 0.0 {
                    soul.amount = soul.amount_dst;
                }
                Ok(None)
            },
            { "args": ["gain", "smooth"] },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| { Ok(Some(json!(soul.amount))) },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                soul.amount = body.arg(0)?;
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
        self.amount = self.smooth * self.amount + (1.0 - self.smooth) * self.amount_dst;
    }
}
