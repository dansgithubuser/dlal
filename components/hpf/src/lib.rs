use dlal_component_base::{arg_num, command, gen_component, join, json, uni, View};

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    a: f32,
    x: f32,
    y: f32,
    output: Option<View>,
}

gen_component!(Specifics, {"in": [], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            a: 0.05,
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
                if let Ok(highness) = arg_num::<f32>(&body, 0) {
                    soul.a = 1.0 - highness;
                }
                Ok(Some(json!(1.0 - soul.a)))
            },
            {
                "args": [{
                    "name": "highness",
                    "optional": true,
                    "range": "[0, 1]",
                }],
            }
        );
        command!(
            commands,
            "to_json",
            |soul, _body| { Ok(Some(json!(soul.a.to_string()))) },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                soul.a = arg_num(&body, 0)?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        if let Some(output) = &self.output {
            let audio = output.audio(self.samples_per_evaluation).unwrap();
            for i in 0..self.samples_per_evaluation {
                let x = audio[i];
                audio[i] = self.a * (self.y + x - self.x);
                self.x = x;
                self.y = audio[i];
            }
        }
    }
}
