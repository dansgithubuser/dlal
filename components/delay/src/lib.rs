use dlal_component_base::{command, gen_component, join, json, marg, uni, View};

use std::vec::Vec;

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    gain_x: f32,
    gain_y: f32,
    gain_o: f32,
    audio: Vec<f32>,
    index: usize,
    output: Option<View>,
}

gen_component!(Specifics, {"in": [], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            gain_x: 1.0,
            gain_y: 0.0,
            gain_o: 1.0,
            audio: vec![0.0; 22050],
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
            "resize",
            |soul, body| {
                if let Ok(v) = marg!(arg_num &body, 0) {
                    soul.audio.resize(v, 0.0);
                }
                Ok(Some(json!(soul.audio.len())))
            },
            {
                "args": [{
                    "name": "size",
                    "optional": true,
                }],
            },
        );
        command!(
            commands,
            "gain_x",
            |soul, body| {
                if let Ok(v) = marg!(arg_num &body, 0) {
                    soul.gain_x = v;
                }
                Ok(Some(json!(soul.gain_x)))
            },
            {
                "args": [{
                    "name": "gain_x",
                    "optional": true,
                    "desc": "input",
                    "default": "1.0",
                }],
            },
        );
        command!(
            commands,
            "gain_y",
            |soul, body| {
                if let Ok(v) = marg!(arg_num &body, 0) {
                    soul.gain_y = v;
                }
                Ok(Some(json!(soul.gain_y)))
            },
            {
                "args": [{
                    "name": "gain_y",
                    "optional": true,
                    "desc": "feedback",
                    "default": "0.0",
                }],
            },
        );
        command!(
            commands,
            "gain_o",
            |soul, body| {
                if let Ok(v) = marg!(arg_num &body, 0) {
                    soul.gain_o = v;
                }
                Ok(Some(json!(soul.gain_o)))
            },
            {
                "args": [{
                    "name": "gain_o",
                    "optional": true,
                    "desc": "output",
                    "default": "1.0",
                }],
            },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| {
                Ok(Some(json!({
                    "size": soul.audio.len(),
                    "gain_x": soul.gain_x,
                    "gain_y": soul.gain_y,
                    "gain_o": soul.gain_o,
                })))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                let j = marg!(arg &body, 0)?;
                soul.audio.resize(marg!(json_num marg!(json_get j, "size")?)?, 0.0);
                soul.gain_x = marg!(json_num marg!(json_get j, "gain_x")?)?;
                soul.gain_y = marg!(json_num marg!(json_get j, "gain_y")?)?;
                soul.gain_o = marg!(json_num marg!(json_get j, "gain_o")?)?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        let audio = match &self.output {
            Some(output) => output.audio(self.samples_per_evaluation).unwrap(),
            None => return,
        };
        for i in 0..self.samples_per_evaluation {
            let x = audio[i];
            let echo = self.audio[self.index] * self.gain_o;
            audio[i] += echo;
            self.audio[self.index] = x * self.gain_x + echo * self.gain_y;
            self.index += 1;
            self.index %= self.audio.len();
        }
    }
}
