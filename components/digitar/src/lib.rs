use dlal_component_base::{component, serde_json, CmdResult};

#[derive(Default)]
struct Note {
    on: bool,
    excitement: f32,
    release: f32,
    delay: Vec<f32>,
    index: f32,
    step: f32,
    y: f32,
    lowness: f32,
    feedback: f32,
    freq: f32,
}

impl Note {
    fn new(freq: f32, sample_rate: u32) -> Self {
        let size = sample_rate as f32 / freq;
        let delay_len = size as usize;
        Self {
            release: freq / sample_rate as f32,
            delay: (0..delay_len).map(|_| 0.0).collect(),
            step: delay_len as f32 / size,
            freq,
            ..Default::default()
        }
    }

    fn on(&mut self, vol: f32, lowness: f32, feedback: f32) {
        self.on = true;
        self.excitement = vol;
        self.lowness = lowness.powf(self.freq / 440.0); // high freq, low lowness
        self.feedback = feedback.powf(440.0 / self.freq); // high freq, high feedback
    }

    fn off(&mut self) {
        self.on = false;
        for i in self.delay.iter_mut() {
            *i = 0.0;
        }
        self.index = 0.0;
        self.y = 0.0;
    }

    fn advance(&mut self) -> f32 {
        // delay output
        let delay_out = self.delay[(self.index as usize + 1) % self.delay.len()];
        // lpf update and output
        self.y = self.lowness * self.y + (1.0 - self.lowness) * delay_out;
        // final output
        let out = self.y + self.excitement;
        // update excitement
        if self.excitement > self.release {
            self.excitement -= self.release;
        } else {
            self.excitement = 0.0;
        }
        // update delay
        self.delay[self.index as usize] = out * self.feedback;
        self.index += self.step;
        if self.index as usize >= self.delay.len() {
            self.index -= self.delay.len() as f32;
        }
        // return final output
        out
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
