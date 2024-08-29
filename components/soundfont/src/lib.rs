use dlal_component_base::{component, serde_json, Body, CmdResult};

use rustysynth;

use std::fs::File;
use std::sync::Arc;

component!(
    {"in": ["midi"], "out": ["audio"]},
    [
        "run_size",
        "sample_rate",
        "uni",
        "check_audio",
        {"name": "field_helpers", "fields": ["soundfont_path"], "kinds": ["r", "json"]},
    ],
    {
        soundfont_path: String,
        synth: Option<rustysynth::Synthesizer>,
        buffer: Vec<f32>,
    },
    {
        "soundfont_load": {
            "args": ["path"],
        },
    },
);

impl ComponentTrait for Component {
    fn run(&mut self) {
        let synth = match self.synth.as_mut() {
            Some(synth) => synth,
            _ => return,
        };
        let audio = match &self.output {
            Some(output) => output.audio(self.run_size).unwrap(),
            None => return,
        };
        synth.render(audio, &mut self.buffer);
    }

    fn midi(&mut self, msg: &[u8]) {
        let synth = match self.synth.as_mut() {
            Some(synth) => synth,
            _ => return,
        };
        if msg.len() < 3 {
            return;
        }
        synth.process_midi_message(
            (msg[0] & 0x0f) as i32,
            (msg[0] & 0xf0) as i32,
            msg[1] as i32,
            msg[2] as i32,
        );
    }

    fn join(&mut self, _body: serde_json::Value) -> CmdResult {
        self.buffer.resize(self.run_size, 0.0);
        if !self.soundfont_path.is_empty() {
            self.soundfont_load()
        } else {
            Ok(None)
        }
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        field_helper_from_json!(self, body);
        if !self.soundfont_path.is_empty() {
            self.soundfont_load()
        } else {
            Ok(None)
        }
    }
}

impl Component {
    fn soundfont_load_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.soundfont_path = body.arg(0)?;
        self.soundfont_load()?;
        Ok(None)
    }

    fn soundfont_load(&mut self) -> CmdResult {
        let mut file = File::open(&self.soundfont_path)?;
        let soundfont = Arc::new(rustysynth::SoundFont::new(&mut file)?);
        let mut settings = rustysynth::SynthesizerSettings::new(self.sample_rate as i32);
        settings.block_size = self.run_size;
        self.synth = Some(rustysynth::Synthesizer::new(&soundfont, &settings)?);
        Ok(None)
    }
}
