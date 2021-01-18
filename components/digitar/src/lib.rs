use dlal_component_base::{component, serde_json, CmdResult};

#[derive(Default)]
struct Note {
    on: bool,
    wavetable: Vec<f32>,
    index: f32,
    step: f32,
    lowness: f32,
    feedback: f32,
    freq: f32,
}

impl Note {
    fn new(freq: f32, sample_rate: u32) -> Self {
        let period = sample_rate as f32 / freq;
        let size = period as usize + 1;
        Self {
            wavetable: vec![0.0; size],
            step: size as f32 / period,
            freq,
            ..Default::default()
        }
    }

    fn on(&mut self, vol: f32, lowness: f32, feedback: f32) {
        self.on = true;
        let size = self.wavetable.len();
        for i in 0..size {
            self.wavetable[i] = vol * (2 * i) as f32 / size as f32;
            if i > size / 2 {
                self.wavetable[i] -= 2.0 * vol;
            }
        }
        self.index = 0.0;
        self.lowness = lowness.powf(self.freq / 440.0); // high freq, low lowness
        self.feedback = feedback.powf(440.0 / self.freq); // high freq, high feedback
    }

    fn off(&mut self) {
        self.on = false;
    }

    fn advance(&mut self) -> f32 {
        let index = self.index as usize;
        let size = self.wavetable.len();
        // sample wavetable
        let sample = {
            let a = self.wavetable[(index + 0) % size];
            let b = self.wavetable[(index + 1) % size];
            let t = self.index - index as f32;
            (1.0 - t) * a + t * b
        };
        // update index and wavetable
        self.index += self.step;
        let next = self.index as usize;
        for i in index..next {
            let b = self.wavetable[(i + size - 1) % size];
            let f = self.wavetable[(i + size + 1) % size];
            let i = i % size;
            self.wavetable[i] = (1.0 - self.lowness) * self.wavetable[i] + self.lowness * (b + f) / 2.0;
            self.wavetable[i] *= self.feedback;
        }
        if next >= size {
            self.index -= size as f32;
        }
        // return sample
        sample
    }
}

component!(
    {"in": ["midi"], "out": ["audio"]},
    [
        "run_size",
        "sample_rate",
        "uni",
        "check_audio",
        {"name": "field_helpers", "fields": ["lowness", "feedback"], "kinds": ["rw", "json"]},
    ],
    {
        lowness: f32,
        feedback: f32,
        notes: Vec<Note>,
    },
    {
        "lowness": {
            "args": [
                {
                    "name": "lowness",
                    "optional": true,
                    "default": 0.5,
                    "desc": "lowness of low pass filter applied to excitation",
                },
            ],
        },
        "feedback": {
            "args": [
                {
                    "name": "feedback",
                    "optional": true,
                    "default": 0.98,
                    "desc": "amount of feedback applied to excitation",
                },
            ],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.lowness = 0.5;
        self.feedback = 0.98;
    }

    fn join(&mut self, _body: serde_json::Value) -> CmdResult {
        self.notes = (0..128)
            .map(|i| {
                Note::new(
                    440.0 * (2.0 as f32).powf((i as f32 - 69.0) / 12.0),
                    self.sample_rate,
                )
            })
            .collect();
        Ok(None)
    }

    fn run(&mut self) {
        let audio = match &self.output {
            Some(output) => output.audio(self.run_size).unwrap(),
            None => return,
        };
        for note in &mut self.notes {
            if !note.on {
                continue;
            }
            for i in audio.iter_mut() {
                *i += note.advance();
            }
        }
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
                    self.notes[msg[1] as usize].on(msg[2] as f32 / 127.0, self.lowness, self.feedback);
                }
            }
            _ => {}
        }
    }
}
