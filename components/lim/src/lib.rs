use dlal_component_base::{
    command,
    gen_component,
    join,
    json,
    marg,
    multi,
    View,
};

use std::vec::Vec;

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    soft: f32,
    soft_gain: f32,
    hard: f32,
    outputs: Vec<View>,
}

gen_component!(Specifics, {"in": [], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            soft: 0.4,
            soft_gain: 0.5,
            hard: 0.5,
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
        multi!(connect commands, true);
        command!(
            commands,
            "soft",
            |soul, body| {
                if let Ok(v) = marg!(arg_num &body, 0) {
                    soul.soft = v;
                }
                Ok(Some(json!(soul.soft)))
            },
            {
                "args": [{
                    "name": "soft",
                    "optional": true,
                }],
            },
        );
        command!(
            commands,
            "soft_gain",
            |soul, body| {
                if let Ok(v) = marg!(arg_num &body, 0) {
                    soul.soft_gain = v;
                }
                Ok(Some(json!(soul.soft_gain)))
            },
            {
                "args": [{
                    "name": "soft_gain",
                    "optional": true,
                }],
            },
        );
        command!(
            commands,
            "hard",
            |soul, body| {
                if let Ok(v) = marg!(arg_num &body, 0) {
                    soul.hard = v;
                    if soul.soft > soul.hard {
                        soul.soft = soul.hard;
                    }
                }
                Ok(Some(json!(soul.hard)))
            },
            {
                "args": [{
                    "name": "hard",
                    "optional": true,
                }],
            },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| {
                Ok(Some(json!({
                    "soft": soul.soft,
                    "soft_gain": soul.soft_gain,
                    "hard": soul.hard,
                })))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                let j = marg!(arg &body, 0)?;
                soul.soft = marg!(json_num marg!(json_get j, "soft")?)?;
                soul.soft_gain = marg!(json_num marg!(json_get j, "soft_gain")?)?;
                soul.hard = marg!(json_num marg!(json_get j, "hard")?)?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        for output in &self.outputs {
            let audio = output.audio(self.samples_per_evaluation).unwrap();
            for i in audio {
                if *i > self.soft {
                    *i = self.soft + (*i - self.soft) * self.soft_gain;
                    if *i > self.hard {
                        *i = self.hard;
                    }
                } else if *i < -self.soft {
                    *i = -self.soft + (*i + self.soft) * self.soft_gain;
                    if *i < -self.hard {
                        *i = -self.hard;
                    }
                }
            }
        }
    }
}
