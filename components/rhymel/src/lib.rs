use dlal_component_base::{gen_component, join, multi, View};

use std::vec::Vec;

const SENTINEL: u8 = 0xff;

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    sample_rate: u32,

    /*
    We have three states, with transitions as follows.

    fresh
    |
    +--> note, when a note is played
            - rhythm: start E5 with same velocity
            - store the number
            - match pitch to note

    note
    |
    +--> note, when a note is played
    |       - rhythm: forward the velocity
    |       - store the number
    |       - match pitch to note
    +--> grace, when the stored note ends
            - store the velocity
            - start silence timer

    grace
    |
    +--> note, when a note is played
    |       - rhythm: forward the velocity
    |       - store the number
    |       - match pitch to note
    |       - forget the velocity
    +--> fresh, when silence timer exceeds grace period
            - rhythm: end E5 with stored velocity
            - forget the note
            - forget the velocity

    The pitch is always equal to that of the stored note's.

    By remembering and forgetting carefully, we can keep track of state implicitly.
    if we remember a velocity  { grace }
    else if we remember a note { note }
    else                       { fresh }
    */
    note: u8,
    pitch: f32,
    velocity: u8,
    silence: f32,

    grace: f32,
    outputs: Vec<View>,
}

gen_component!(Specifics, {"in": ["midi"], "out": ["midi", "audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            note: SENTINEL,
            velocity: SENTINEL,
            grace: 0.1,
            ..Default::default()
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                join!(samples_per_evaluation soul, body);
                join!(sample_rate soul, body);
                Ok(None)
            },
            ["samples_per_evaluation", "sample_rate"],
        );
        multi!(connect commands, false);
    }

    fn evaluate(&mut self) {
        // grace
        if self.velocity != SENTINEL {
            self.silence += self.samples_per_evaluation as f32 / self.sample_rate as f32;
            // grace -> fresh
            if self.silence > self.grace {
                multi!(midi [0x80, 0x40, self.velocity], self.outputs);
                self.note = SENTINEL;
                self.velocity = SENTINEL;
            }
        }
        // send pitch as control voltage to outputs
        for output in &self.outputs {
            if let Some(audio) = output.audio(self.samples_per_evaluation) {
                for i in 0..self.samples_per_evaluation {
                    audio[i] += self.pitch;
                }
            }
        }
    }

    fn midi(&mut self, msg: &[u8]) {
        if msg.len() < 3 {
            return;
        }
        let type_nibble = msg[0] & 0xf0;
        if type_nibble == 0x80 || type_nibble == 0x90 && msg[2] == 0 {
            // note -> grace
            if msg[1] == self.note {
                self.velocity = msg[2];
                self.silence = 0.0;
            }
        } else if type_nibble == 0x90 {
            // fresh -> note
            if self.note == SENTINEL && self.velocity == SENTINEL {
                multi!(midi [0x90, 0x40, msg[2]], self.outputs);
                self.note = msg[1];
            }
            // (note, grace) -> note
            else {
                multi!(midi [0xa0, 0x40, msg[2]], self.outputs);
                self.note = msg[1];
                self.velocity = SENTINEL;
            }
            // pitch
            self.pitch = self.note as f32 / 128.0;
        }
    }
}
