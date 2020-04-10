use dlal_component_base::{arg_num, command, gen_component, join, json, uni, View};

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    lowness: f32,
    y: f32,
    output: Option<View>,
}

gen_component!(Specifics, {"in": [], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            lowness: 0.95,
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
            "set",
            |soul, body| {
                if let Ok(lowness) = arg_num::<f32>(&body, 0) {
                    soul.lowness = lowness;
                }
                Ok(Some(json!(soul.lowness)))
            },
            {
                "args": [{
                    "name": "lowness",
                    "range": "[0, 1]",
                }],
            }
        );
        command!(
            commands,
            "to_json",
            |soul, _body| { Ok(Some(json!(soul.lowness.to_string()))) },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                soul.lowness = arg_num(&body, 0)?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        if let Some(output) = &self.output {
            let audio = output.audio(self.samples_per_evaluation).unwrap();
            for i in 0..self.samples_per_evaluation {
                audio[i] = (1.0 - self.lowness) * audio[i] + self.lowness * self.y;
                self.y = audio[i];
            }
        }
    }
}
