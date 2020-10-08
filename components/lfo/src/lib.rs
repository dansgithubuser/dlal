use dlal_component_base::{
    command, gen_component, join, json, uni, View, Body, serde_json,
};

use std::f32::consts::PI;

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    sample_rate: u32,
    freq: f32,
    amp: f32,
    phase: f32,
    output: Option<View>,
}

gen_component!(Specifics, {"in": [], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            freq: 1.0,
            amp: 0.1,
            ..Default::default()
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                soul.samples_per_evaluation = body.kwarg("samples_per_evaluation")?;
                soul.sample_rate = body.kwarg("sample_rate")?;
                Ok(None)
            },
            ["samples_per_evaluation", "sample_rate"],
        );
        uni!(connect commands, true);
        command!(
            commands,
            "freq",
            |soul, body| {
                if let Ok(v) = body.arg(0) {
                    soul.freq = v;
                }
                Ok(Some(json!(soul.freq)))
            },
            {
                "args": [{
                    "name": "freq",
                    "optional": true,
                }],
            },
        );
        command!(
            commands,
            "amp",
            |soul, body| {
                if let Ok(v) = body.arg(0) {
                    soul.amp = v;
                }
                Ok(Some(json!(soul.amp)))
            },
            {
                "args": [{
                    "name": "amp",
                    "optional": true,
                }],
            },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| {
                Ok(Some(json!({
                    "freq": soul.freq,
                    "amp": soul.amp,
                })))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                let j = body.arg::<serde_json::Value>(0)?;
                soul.freq = j.at("freq")?;
                soul.amp = j.at("amp")?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        let step = 2.0 * PI * self.freq / self.sample_rate as f32;
        if let Some(output) = self.output.as_ref() {
            let audio = output.audio(self.samples_per_evaluation).unwrap();
            for i in 0..self.samples_per_evaluation {
                audio[i] += self.amp * self.phase.sin();
                self.phase += step;
            }
        } else {
            self.phase += step * self.samples_per_evaluation as f32;
        }
        if self.phase > 2.0 * PI {
            self.phase -= 2.0 * PI;
        }
    }
}
