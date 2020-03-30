use dlal_component_base::{gen_component, json, kwarg_num, multiconnect, View};

use std::vec::Vec;

pub struct Specifics {
    audio: Vec<f32>,
    views: Vec<View>,
}

gen_component!(Specifics);

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            audio: Vec::new(),
            views: Vec::with_capacity(1),
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        commands.insert(
            "join",
            Command {
                func: Box::new(|soul, body| {
                    soul.audio
                        .resize(kwarg_num(&body, "samples_per_evaluation")?, 0.0);
                    Ok(None)
                }),
                info: json!({
                    "kwargs": ["samples_per_evaluation"],
                }),
            },
        );
        multiconnect!(commands, true);
    }

    fn evaluate(&mut self) {
        for view in &self.views {
            let audio = view.audio(self.audio.len()).unwrap();
            for i in 0..self.audio.len() {
                audio[i] += self.audio[i];
            }
        }
    }

    fn audio(&mut self) -> Option<&mut [f32]> {
        Some(self.audio.as_mut_slice())
    }
}
