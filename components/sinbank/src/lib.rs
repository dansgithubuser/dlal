use dlal_component_base::{component, serde_json, Body, CmdResult};

use std::f32;
use std::f32::consts::PI;

const BIN_SIZE: f32 = 100.0;

component!(
    {"in": ["midi", "cmd"], "out": ["audio"]},
    [
        "run_size",
        "sample_rate",
        "uni",
        "check_audio",
        {"name": "field_helpers", "fields": ["bend", "phase"], "kinds": ["rw"]},
    ],
    {
        spectrum: Vec<f32>,
        bend: f32,
        step: f32,
        phase: f32,
        vol: f32,
        rpn: u16,              //registered parameter number
        pitch_bend_range: f32, //MIDI RPN 0x0000
    },
    {
        "spectrum": {
            "args": [{
                "name": "spectrum",
                "type": "array",
                "element": "float",
                "desc": "An array of amplitudes of 100 Hz bins.",
            }],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.spectrum = vec![0.01;   60];
        self.bend = 1.0;
        self.pitch_bend_range = 2.0;
    }

    fn run(&mut self) {
        let output = match self.output.as_ref() {
            Some(v) => v,
            None => return,
        };
        let freq = self.step / (2.0 * PI) * self.sample_rate as f32;
        for i in output.audio(self.run_size).unwrap() {
            *i += self.vol
                * (1..std::cmp::min(((self.spectrum.len() as f32 - 0.5) * BIN_SIZE / freq) as usize, 64))
                    .map(|j| {
                        self.spectrum[(j as f32 * freq / BIN_SIZE + 0.5) as usize]
                            * (self.phase * j as f32).sin()
                    })
                    .sum::<f32>();
            self.phase += self.step * self.bend;
        }
        let p = 2.0 * self.run_size as f32 * PI;
        if self.phase > p {
            self.phase -= p;
        }
    }

    fn midi(&mut self, msg: &[u8]) {
        if msg.len() < 3 {
            return;
        }
        match msg[0] & 0xf0 {
            0x80 => {
                self.vol = 0.0;
            }
            0x90 => {
                self.step = 2.0 * PI * 440.0 * 2.0_f32.powf((msg[1] as f32 - 69.0) / 12.0)
                    / self.sample_rate as f32;
                self.vol = msg[2] as f32 / 127.0;
            }
            0xa0 => {
                self.vol = msg[2] as f32 / 127.0;
            }
            0xb0 => match msg[1] {
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
            },
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

impl Component {
    fn spectrum_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.spectrum = body.arg(0)?;
        Ok(None)
    }
}
