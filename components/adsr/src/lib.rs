use dlal_component_base::{Body, command, gen_component, join, json, uni, View, serde_json};

enum Stage {
    A,
    D,
    S,
    R,
}

impl Default for Stage {
    fn default() -> Self {
        Stage::R
    }
}

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    a: f32,
    d: f32,
    s: f32,
    r: f32,
    stage: Stage,
    vol: f32,
    output: Option<View>,
}

gen_component!(Specifics, {"in": ["midi"], "out": ["audio"]});

macro_rules! stage_command {
    ($commands:ident, $name:literal, $member:tt, ($($info:tt)+)) => {
        command!(
            $commands,
            $name,
            |soul, body| {
                if let Ok(v) = body.arg(0) {
                    soul.$member = v;
                }
                Ok(Some(json!(soul.$member)))
            },
            {"args": [$($info)+]},
        );
    }
}

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            a: 0.01,
            d: 0.01,
            s: 0.5,
            r: 0.01,
            ..Default::default()
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                soul.samples_per_evaluation = body.kwarg("samples_per_evaluation")?;
                Ok(None)
            },
            ["samples_per_evaluation"],
        );
        uni!(connect commands, true);
        stage_command!(commands, "a", a, ({
            "name": "amount",
            "desc": "attack rate",
            "units": "amplitude per sample",
            "range": "(0, 1]",
        }));
        stage_command!(commands, "d", d, ({
            "name": "amount",
            "desc": "decay rate",
            "units": "amplitude per sample",
            "range": "(0, 1]",
        }));
        stage_command!(commands, "s", s, ({
            "name": "amount",
            "desc": "sustain level",
            "range": "[0, 1]",
        }));
        stage_command!(commands, "r", r, ({
            "name": "amount",
            "desc": "release rate",
            "units": "amplitude per sample",
            "range": "(0, 1]",
        }));
        command!(
            commands,
            "reset",
            |soul, _body| {
                soul.stage = Stage::R;
                soul.vol = 0.0;
                Ok(None)
            },
            {},
        );
        command!(
            commands,
            "to_json",
            |soul, _body| {
                Ok(Some(json!({
                    "a": soul.a,
                    "d": soul.d,
                    "s": soul.s,
                    "r": soul.r,
                })))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                let j: serde_json::Value = body.arg(0)?;
                soul.a = j.at("a")?;
                soul.d = j.at("d")?;
                soul.s = j.at("s")?;
                soul.r = j.at("r")?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        let audio = match &self.output {
            Some(output) => output.audio(self.samples_per_evaluation).unwrap(),
            None => return,
        };
        for i in audio {
            match self.stage {
                Stage::A => {
                    self.vol += self.a;
                    if self.vol > 1.0 {
                        self.vol = 1.0;
                        self.stage = Stage::D;
                    }
                }
                Stage::D => {
                    self.vol -= self.d;
                    if self.vol < self.s {
                        self.vol = self.s;
                        self.stage = Stage::S;
                    }
                }
                Stage::S => (),
                Stage::R => {
                    self.vol -= self.r;
                    if self.vol < 0.0 {
                        self.vol = 0.0;
                    }
                }
            }
            *i += self.vol;
        }
    }

    fn midi(&mut self, msg: &[u8]) {
        if msg.len() < 3 {
            return;
        }
        let type_nibble = msg[0] & 0xf0;
        if type_nibble == 0x80 || type_nibble == 0x90 && msg[2] == 0 {
            self.stage = Stage::R;
        } else if type_nibble == 0x90 {
            self.stage = Stage::A;
        }
    }
}
