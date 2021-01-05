use dlal_component_base::component;

component!(
    {"in": ["midi"], "out": ["midi"]},
    [
        "run_size",
        "sample_rate",
        "multi",
        {"name": "field_helpers", "fields": ["rate"], "kinds": ["rw", "json"]},
    ],
    {
        notes: Vec<[u8; 2]>,
        note: usize,
        note_last: u8,
        phase: f32,
        rate: f32,
    },
    {},
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.rate = 30.0;
    }

    fn run(&mut self) {
        self.phase += self.rate / self.sample_rate as f32 * self.run_size as f32;
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

impl Component {
    fn midi_for_note(&mut self) {
        let note = self.notes[self.note];
        for output in &self.outputs {
            output.midi(&[0x90, note[0], note[1]]);
            output.midi(&[0x80, self.note_last, 0]);
        }
        self.note_last = note[0];
    }
}
