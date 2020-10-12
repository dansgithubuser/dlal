use dlal_component_base::{component, serde_json, Body, CmdResult};

const SENTINEL: u8 = 0xff;

component!(
    {"in": ["midi"], "out": ["midi", "audio"]},
    ["samples_per_evaluation", "sample_rate", "multi"],
    {
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
    },
    {},
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.note = SENTINEL;
        self.velocity = SENTINEL;
        self.grace = 0.1;
    }

    fn evaluate(&mut self) {
        // grace
        if self.velocity != SENTINEL {
            self.silence += self.samples_per_evaluation as f32 / self.sample_rate as f32;
            // grace -> fresh
            if self.silence > self.grace {
                self.multi_midi(&[0x80, 0x40, self.velocity]);
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
                self.multi_midi(&[0x90, 0x40, msg[2]]);
                self.note = msg[1];
            }
            // (note, grace) -> note
            else {
                self.multi_midi(&[0xa0, 0x40, msg[2]]);
                self.note = msg[1];
                self.velocity = SENTINEL;
            }
            // pitch
            self.pitch = self.note as f32 / 128.0;
        }
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(None)
    }

    fn from_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(None)
    }
}
