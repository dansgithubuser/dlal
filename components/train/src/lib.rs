use dlal_component_base::{command, err, gen_component, join, json, marg, uni, View};

use std::vec::Vec;

// ===== note ===== //
#[derive(Default)]
struct Note {
    step: f32,
    vol: f32,
    on: bool,
    phase: f32,
    index: usize,
}

impl Note {
    fn new(step: f32) -> Self {
        Self {
            step,
            ..Default::default()
        }
    }

    fn on(&mut self, vol: f32) {
        self.vol = vol;
        self.on = true;
        self.phase = 0.0;
        self.index = 0;
    }

    fn off(&mut self) {
        self.on = false;
    }

    fn advance(&mut self, impulse: &[f32]) -> f32 {
        self.phase += self.step;
        if self.phase >= 1.0 {
            self.phase -= 1.0;
            self.index = 1;
            return self.vol * impulse[0];
        }
        if self.index != 0 {
            if self.index == impulse.len() {
                self.index = 0;
            } else {
                let amp = self.vol * impulse[self.index];
                self.index += 1;
                return amp;
            }
        }
        0.0
    }
}

// ===== components ===== //
#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    sample_rate: u32,
    impulse: Vec<f32>,
    notes: Vec<Note>,
    output: Option<View>,
}

gen_component!(Specifics, {"in": ["midi"], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            impulse: vec![1.0],
            ..Default::default()
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                join!(samples_per_evaluation soul, body);
                join!(sample_rate soul, body);
                soul.notes = (0..128)
                    .map(|i| {
                        Note::new(
                            440.0 * (2.0 as f32).powf((i as f32 - 69.0) / 12.0)
                                / soul.sample_rate as f32,
                        )
                    })
                    .collect();
                Ok(None)
            },
            ["samples_per_evaluation", "sample_rate"],
        );
        uni!(connect commands, true);
        command!(
            commands,
            "impulse",
            |soul, body| {
                if let Ok(v) = marg!(arg &body, 0) {
                    let impulse = marg!(json_nums &v)?;
                    if !impulse.is_empty() {
                        soul.impulse = impulse;
                    } else {
                        return err!("impulse must have at least one element");
                    }
                }
                Ok(Some(json!(soul.impulse)))
            },
            {
                "args": [{
                    "name": "impulse",
                    "optional": true,
                }],
            },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| {
                Ok(Some(json!({
                    "impulse": soul.impulse,
                })))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                let j = marg!(arg &body, 0)?;
                soul.impulse = marg!(json_f32s marg!(json_get j, "value")?)?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn midi(&mut self, msg: &[u8]) {
        if msg.len() < 3 {
            return;
        }
        match msg[0] & 0xf0 {
            0x80 => {
                self.notes[msg[1] as usize].off();
            }
            0x90 => {
                if msg[2] == 0 {
                    self.notes[msg[1] as usize].off();
                } else {
                    self.notes[msg[1] as usize].on(msg[2] as f32 / 127.0);
                }
            }
            _ => {}
        }
    }

    fn evaluate(&mut self) {
        let audio = match &self.output {
            Some(output) => output.audio(self.samples_per_evaluation).unwrap(),
            None => return,
        };
        for note in &mut self.notes {
            if !note.on && note.index == 0 {
                continue;
            }
            for i in audio.iter_mut() {
                *i += note.advance(&self.impulse);
            }
        }
    }
}
