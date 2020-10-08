use dlal_component_base::{command, gen_component, join, json, multi, View, Body};

#[derive(Default)]
pub struct Specifics {
    audio: Vec<f32>,
    value: f32,
    outputs: Vec<View>,
}

gen_component!(Specifics, {"in": ["audio"], "out": ["audio"]});

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
                soul.audio
                    .resize(body.kwarg("samples_per_evaluation")?, 0.0);
                Ok(None)
            },
            ["samples_per_evaluation"],
        );
        multi!(connect commands, true);
        command!(
            commands,
            "value",
            |soul, _body| {
                Ok(Some(json!(soul.value)))
            },
            { "args": [] },
        );
    }

    fn audio(&mut self) -> Option<&mut [f32]> {
        Some(self.audio.as_mut_slice())
    }

    fn evaluate(&mut self) {
        for i in &mut self.audio {
            self.value *= 0.999;
            if self.value < i.abs() {
                self.value = i.abs();
            }
            *i = self.value;
        }
        multi!(audio self.audio, self.outputs, self.audio.len());
        for i in &mut self.audio {
            *i = 0.0;
        }
    }
}
