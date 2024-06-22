use dlal_component_base::{component, serde_json, Arg, Body, CmdResult};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
enum Excitation {
    Saw,
    Hammer { contact: f32, offset: f32 },
}

impl Default for Excitation {
    fn default() -> Self {
        Excitation::Saw
    }
}

impl Arg for Excitation {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        serde_json::from_str(&value.to_string()).ok()
    }
}

#[derive(Default)]
struct Note {
    on: bool,
    done: bool,
    wavetable: Vec<f32>,
    x: f32,
    index: f32,
    step: f32,
    lowness: f32,
    feedback: f32,
    release: f32,
    freq: f32,
    sample_rate: u32,
    sum: f32,
    hammer_contact: u32,
    hammer_offset: usize,
    hammer_vol: f32,
    hammer_displacement: u32,
    bend: f32,
}

impl Note {
    fn new(freq: f32, sample_rate: u32) -> Self {
        let period = sample_rate as f32 / freq;
        let size = period as usize + 1;
        Self {
            wavetable: vec![0.0; size],
            step: size as f32 / period,
            freq,
            sample_rate,
            ..Default::default()
        }
    }

    fn on(&mut self, vol: f32, lowness: f32, feedback: f32, excitation: &Excitation, bend: f32) {
        self.on = true;
        self.done = false;
        let size = self.wavetable.len();
        match excitation {
            Excitation::Saw => {
                for i in 0..size {
                    self.wavetable[i] = vol * (2 * i) as f32 / size as f32;
                    if i > size / 2 {
                        self.wavetable[i] -= 2.0 * vol;
                    }
                }
            }
            Excitation::Hammer { contact, offset } => {
                let length = 2093.00 / self.freq;
                self.hammer_offset = ((offset / length * size as f32) as usize).min(size);
                self.hammer_contact = (contact * self.sample_rate as f32) as u32;
                self.hammer_vol = vol;
                self.hammer_displacement = 0;
            }
        }
        self.index = 0.0;
        self.lowness = lowness.powf(self.freq / 440.0); // high freq, low lowness
        self.feedback = feedback.powf(440.0 / self.freq); // high freq, high feedback
        self.bend = bend;
    }

    fn off(&mut self, release: f32) {
        self.on = false;
        self.release = release;
    }

    fn advance(&mut self) -> f32 {
        let index = self.index as usize;
        let size = self.wavetable.len();
        // hammer
        if self.hammer_contact != 0 {
            if self.hammer_displacement < self.hammer_contact {
                self.hammer_displacement += 1;
                let d = self.hammer_vol / self.hammer_contact as f32;
                for i in 0..self.hammer_offset {
                    self.wavetable[i] += d * (2.0 * i as f32 / self.hammer_offset as f32 - 1.0);
                }
                for i in self.hammer_offset..size {
                    self.wavetable[i] += d * (2.0 * (1.0 - (i - self.hammer_offset) as f32 / (size - self.hammer_offset) as f32) - 1.0);
                }
            } else {
                self.hammer_contact = 0;
            }
        }
        // sample wavetable
        let sample = {
            let a = self.wavetable[(index + 0) % size];
            let b = self.wavetable[(index + 1) % size];
            let t = self.index - index as f32;
            (1.0 - t) * a + t * b
        };
        // update index and wavetable
        self.index += self.step * self.bend;
        let next = self.index as usize;
        for i in index..next {
            let i = i % size;
            self.x = self.lowness * self.x + (1.0 - self.lowness) * self.wavetable[i];
            self.wavetable[i] = self.x;
            self.wavetable[i] *= if self.on {
                self.feedback
            } else {
                1.0 - self.release
            };
            self.sum += self.wavetable[i].abs();
        }
        if next >= size {
            if self.sum < 0.0001 {
                self.done = true;
            }
            self.sum = 0.0;
            self.index -= size as f32;
        }
        // return sample
        sample
    }

    fn done(&self) -> bool {
        self.done
    }
}

component!(
    {"in": ["midi"], "out": ["audio"]},
    [
        "run_size",
        "sample_rate",
        "uni",
        "check_audio",
        {
            "name": "field_helpers",
            "fields": ["lowness", "feedback", "release", "stay_on"],
            "kinds": ["rw", "json"]
        },
        {
            "name": "field_helpers",
            "fields": ["excitation"],
            "kinds": ["json"]
        },
    ],
    {
        lowness: f32,
        feedback: f32,
        stay_on: bool,
        notes: Vec<Note>,
        excitation: Excitation,
        release: f32,
        rpn: u16,              //registered parameter number
        pitch_bend_range: f32, //MIDI RPN 0x0000
        bend: f32,
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
        "saw": {
            "desc": "Excite each string like a saw wave.",
        },
        "hammer": {
            "desc": "Hammer each string like a piano.",
            "kwargs": [
                {
                    "name": "contact",
                    "default": 0.01,
                    "desc": "How long hammer contacts string for, in seconds.",
                },
                {
                    "name": "offset",
                    "default": 0.5,
                    "desc": "Where the hammer strikes, in highest piano key (MIDI 96, 2093.00 Hz) string-lengths.",
                },
            ],
        },
    },
);

impl Component {
    fn saw_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        self.excitation = Excitation::Saw;
        Ok(None)
    }

    fn hammer_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let contact = body.kwarg("contact").unwrap_or(0.01);
        let offset = body.kwarg("offset").unwrap_or(0.5);
        self.excitation = Excitation::Hammer { contact, offset };
        Ok(None)
    }
}

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.lowness = 0.5;
        self.feedback = 0.98;
        self.release = 1.0;
        self.bend = 1.0;
        self.pitch_bend_range = 2.0;
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
            if note.done() {
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
                if self.stay_on {
                    return;
                }
                self.notes[msg[1] as usize].off(self.release);
            }
            0x90 => {
                if msg[2] == 0 && self.stay_on {
                    return;
                }
                if msg[2] == 0 {
                    self.notes[msg[1] as usize].off(self.release);
                } else {
                    self.notes[msg[1] as usize].on(
                        msg[2] as f32 / 127.0,
                        self.lowness,
                        self.feedback,
                        &self.excitation,
                        self.bend,
                    );
                }
            }
            0xb0 => {
                match msg[1] {
                    0x65 => self.rpn = (msg[2] << 7) as u16,
                    0x64 => self.rpn += msg[2] as u16,
                    0x06 => match self.rpn {
                        0x0000 => self.pitch_bend_range = msg[2] as f32,
                        _ => (),
                    },
                    0x26 => match self.rpn {
                        0x0000 => self.pitch_bend_range += msg[2] as f32 / 100.0,
                        _ => (),
                    },
                    _ => (),
                }
            }
            0xe0 => {
                const CENTER: f32 = 0x2000 as f32;
                let value = (msg[1] as u16 + ((msg[2] as u16) << 7)) as f32;
                let octaves = self.pitch_bend_range * (value - CENTER) / (CENTER * 12.0);
                self.bend = (2.0 as f32).powf(octaves);
            }
            _ => {}
        }
    }
}
