use dlal_component_base::{component, err, json, serde_json, Body, CmdResult};

// ===== note ===== //
#[derive(Default)]
struct Note {
    step: f32,
    vol: f32,
    on: bool,
    phase: f32,
    index: Option<usize>,
}

impl Note {
    fn new(step: f32) -> Self {
        Self {
            step,
            ..Default::default()
        }
    }

    fn on(&mut self, vol: f32) {
        self.vol = vol;
        self.on = true;
        self.phase = 0.0;
        self.index = Some(0);
    }

    fn off(&mut self) {
        self.on = false;
    }

    fn advance(&mut self, impulse: &[f32]) -> f32 {
        self.phase += self.step;
        if self.phase >= 1.0 {
            self.phase -= 1.0;
            self.index = Some(0);
            return self.vol * impulse[0];
        }
        if let Some(index) = self.index {
            if index == impulse.len() {
                self.index = None;
            } else {
                let amp = self.vol * impulse[index];
                self.index = Some(index + 1);
                return amp;
            }
        }
        0.0
    }
}

// ===== component ===== //
component!(
    {"in": ["midi"], "out": ["audio"]},
    ["run_size", "sample_rate", "uni", "check_audio"],
    {
        impulse: Vec<f32>,
        notes: Vec<Note>,
    },
    {
        "impulse": {
            "args": [{
                "name": "impulse",
                "optional": true,
            }],
        },
        "one": {},
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.impulse.push(1.0);
    }

    fn join(&mut self, _body: serde_json::Value) -> CmdResult {
        self.notes = (0..128)
            .map(|i| {
                Note::new(
                    440.0 * (2.0 as f32).powf((i as f32 - 69.0) / 12.0) / self.sample_rate as f32,
                )
            })
            .collect();
        Ok(None)
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

    fn run(&mut self) {
        let audio = match &self.output {
            Some(output) => output.audio(self.run_size).unwrap(),
            None => return,
        };
        for note in &mut self.notes {
            if !note.on && note.index.is_none() {
                continue;
            }
            for i in audio.iter_mut() {
                *i += note.advance(&self.impulse);
            }
        }
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({
            "impulse": self.impulse,
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = body.arg::<serde_json::Value>(0)?;
        self.impulse = j.at("impulse")?;
        Ok(None)
    }
}

impl Component {
    fn impulse_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg::<serde_json::Value>(0) {
            let impulse = v.to::<Vec<_>>()?;
            if !impulse.is_empty() {
                self.impulse = impulse;
            } else {
                return Err(err!("impulse must have at least one element").into());
            }
        }
        Ok(Some(json!(self.impulse)))
    }

    fn one_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        let note = &mut self.notes[0];
        note.vol = 1.0;
        note.phase = 0.0;
        note.index = Some(0);
        Ok(None)
    }
}
