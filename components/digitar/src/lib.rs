use dlal_component_base::{component, serde_json, CmdResult};

#[derive(Default)]
struct Note {
    on: bool,
    excitement: f32,
    release: f32,
    delay: Vec<f32>,
    index: usize,
    y: f32,
}

impl Note {
    fn new(freq: f32, sample_rate: u32) -> Self {
        let size = (sample_rate as f32 / freq) as usize;
        Self {
            release: freq / sample_rate as f32,
            delay: (0..size).map(|_| 0.0).collect(),
            ..Default::default()
        }
    }

    fn on(&mut self, vol: f32) {
        self.on = true;
        self.excitement = vol;
    }

    fn off(&mut self) {
        self.on = false;
        for i in self.delay.iter_mut() {
            *i = 0.0;
        }
        self.index = 0;
        self.y = 0.0;
    }

    fn advance(&mut self, lowness: f32, feedback: f32) -> f32 {
        // delay output
        let delay_out = self.delay[(self.index + 1) % self.delay.len()];
        // lpf update and output
        self.y = lowness * self.y + (1.0 - lowness) * delay_out;
        // final output
        let out = self.y + self.excitement;
        // update excitement
        if self.excitement > self.release {
            self.excitement -= self.release;
        } else {
            self.excitement = 0.0;
        }
        // update delay
        self.delay[self.index] = out * feedback;
        self.index += 1;
        self.index %= self.delay.len();
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
                    "desc": "lowness of low pass filter applied to excitation",
                },
            ],
        },
        "feedback": {
            "args": [
                {
                    "name": "feedback",
                    "optional": true,
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
                *i += note.advance(self.lowness, self.feedback);
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
                    self.notes[msg[1] as usize].on(msg[2] as f32 / 127.0);
                }
            }
            _ => {}
        }
    }
}
