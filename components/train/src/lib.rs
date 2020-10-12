use dlal_component_base::{command, err, gen_component, join, json, uni, View, Body, serde_json, Arg};

// ===== note ===== //
#[derive(Default)]
struct Note {
    step: f32,
    vol: f32,
    on: bool,
    phase: f32,
    index: Option<usize>,
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
        self.index = Some(0);
    }

    fn off(&mut self) {
        self.on = false;
    }

    fn advance(&mut self, impulse: &[f32]) -> f32 {
        self.phase += self.step;
        if self.phase >= 1.0 {
            self.phase -= 1.0;
            self.index = Some(0);
            return self.vol * impulse[0];
        }
        if let Some(index) = self.index {
            if index == impulse.len() {
                self.index = None;
            } else {
                let amp = self.vol * impulse[index];
                self.index = Some(index + 1);
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
                soul.samples_per_evaluation = body.kwarg("samples_per_evaluation")?;
                soul.sample_rate = body.kwarg("sample_rate")?;
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
                if let Ok(v) = body.arg::<serde_json::Value>(0) {
                    let impulse = v.to::<Vec<_>>()?.vec()?;
                    if !impulse.is_empty() {
                        soul.impulse = impulse;
                    } else {
                        Err(err!("impulse must have at least one element"))?;
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
            "one",
            |soul, _body| {
                let note = &mut soul.notes[0];
                note.vol = 1.0;
                note.phase = 0.0;
                note.index = Some(0);
                Ok(None)
            },
            { "args": [] },
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
                let j = body.arg::<serde_json::Value>(0)?;
                soul.impulse = j.at::<Vec<_>>("impulse")?.vec()?;
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
            if !note.on && note.index.is_none() {
                continue;
            }
            for i in audio.iter_mut() {
                *i += note.advance(&self.impulse);
            }
        }
    }
}
