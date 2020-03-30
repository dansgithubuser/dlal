use dlal_component_base::{command, gen_component, kwarg_num, multiconnect, View};

use std::vec::Vec;

pub struct Specifics {
    audio: Vec<f32>,
    outputs: Vec<View>,
}

gen_component!(Specifics);

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            audio: Vec::new(),
            outputs: Vec::with_capacity(1),
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        command!(
            commands,
            "join",
            |soul, body| {
                soul.audio
                    .resize(kwarg_num(&body, "samples_per_evaluation")?, 0.0);
                Ok(None)
            },
            { "kwargs": ["samples_per_evaluation"] },
        );
        multiconnect!(commands, true);
    }

    fn evaluate(&mut self) {
        for output in &self.outputs {
            let audio = output.audio(self.audio.len()).unwrap();
            for i in 0..self.audio.len() {
                audio[i] += self.audio[i];
            }
        }
    }

    fn audio(&mut self) -> Option<&mut [f32]> {
        Some(self.audio.as_mut_slice())
    }
}
