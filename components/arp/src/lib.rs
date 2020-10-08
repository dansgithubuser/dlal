use dlal_component_base::{Body, command, gen_component, join, json, multi, View, serde_json};

#[derive(Default)]
pub struct Specifics {
    notes: Vec<[u8; 2]>,
    note: usize,
    note_last: u8,
    phase: f32,
    rate: f32,
    samples_per_evaluation: usize,
    sample_rate: u32,
    outputs: Vec<View>,
}

impl Specifics {
    fn midi_for_note(&mut self) {
        let note = self.notes[self.note];
        for output in &self.outputs {
            output.midi(&[0x90, note[0], note[1]]);
            output.midi(&[0x80, self.note_last, 0]);
        }
        self.note_last = note[0];
    }
}

gen_component!(Specifics, {"in": ["midi"], "out": ["midi"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            rate: 30.0,
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
        multi!(connect commands, false);
        command!(
            commands,
            "rate",
            |soul, body| {
                if let Ok(v) = body.arg(0) {
                    soul.rate = v;
                }
                Ok(Some(json!(soul.rate)))
            },
            {
                "args": [{
                    "name": "rate",
                    "optional": true,
                }],
            },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| {
                Ok(Some(json!({
                    "rate": soul.rate,
                })))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                let j: serde_json::Value = body.arg(0)?;
                soul.rate = j.at("rate")?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        self.phase += self.rate / self.sample_rate as f32 * self.samples_per_evaluation as f32;
        if self.phase >= 1.0 {
            self.note += 1;
            if self.note >= self.notes.len() {
                self.note = 0;
            }
            if !self.notes.is_empty() {
                self.midi_for_note();
            }
            self.phase -= 1.0;
        }
    }

    #[allow(clippy::collapsible_if)]
    fn midi(&mut self, msg: &[u8]) {
        if msg.len() < 3 {
            return;
        }
        let type_nibble = msg[0] & 0xf0;
        if type_nibble == 0x80 || type_nibble == 0x90 && msg[2] == 0 {
            if let Some(i) = self.notes.iter().position(|i| i[0] == msg[1]) {
                self.notes.remove(i);
                if self.notes.is_empty() {
                    for output in &self.outputs {
                        output.midi(&[0x80, self.note_last, 0]);
                    }
                }
            }
        } else if type_nibble == 0x90 {
            if self.notes.iter().position(|i| i[0] == msg[1]).is_none() {
                self.notes.push([msg[1], msg[2]]);
                if self.notes.len() == 1 {
                    self.note = 0;
                    self.midi_for_note();
                    self.phase = 0.0;
                }
            }
        }
    }
}
