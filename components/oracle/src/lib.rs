use dlal_component_base::{
    command, gen_component, join, json, serde_json,
    multi, View, Body,
};

const MODE_F32: u8 = 0;
const MODE_I32: u8 = 1;
const MODE_PITCH_WHEEL: u8 = 2;

#[derive(Default)]
pub struct Specifics {
    cv: Vec<f32>,
    m: f32,
    b: f32,
    mode: u8,
    format: String,
    outputs: Vec<View>,
    last_error: String,
}

gen_component!(Specifics, {"in": ["audio"], "out": ["cmd", "midi"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            outputs: Vec::with_capacity(1),
            m: 1.0,
            b: 0.0,
            ..Default::default()
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                soul.cv
                    .resize(body.kwarg("samples_per_evaluation")?, 0.0);
                Ok(None)
            },
            ["samples_per_evaluation"],
        );
        multi!(connect commands, false);
        command!(
            commands,
            "format",
            |soul, body| {
                soul.format = body.arg(0)?;
                Ok(Some(json!(soul.format)))
            },
            {
                "args": ["format"],
            },
        );
        command!(
            commands,
            "mode",
            |soul, body| {
                soul.mode = body.arg(0)?;
                Ok(Some(json!(soul.mode)))
            },
            {
                "args": ["mode"],
            },
        );
        command!(
            commands,
            "m",
            |soul, body| {
                soul.m = body.arg(0)?;
                Ok(Some(json!(soul.m)))
            },
            {
                "args": ["m"],
            },
        );
        command!(
            commands,
            "b",
            |soul, body| {
                soul.b = body.arg(0)?;
                Ok(Some(json!(soul.b)))
            },
            {
                "args": ["b"],
            },
        );
        command!(
            commands,
            "last_error",
            |soul, _body| {
                Ok(Some(json!(soul.last_error)))
            },
            {
                "args": [],
            },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| {
                Ok(Some(json!({
                    "m": soul.m,
                    "b": soul.b,
                    "mode": soul.mode,
                    "format": soul.format,
                })))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                let j = body.arg::<serde_json::Value>(0)?;
                soul.m = j.at("m")?;
                soul.b = j.at("b")?;
                soul.mode = j.at("mode")?;
                soul.format = j.at("format")?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        let y = self.m * self.cv[0] + self.b;
        let text = match self.mode {
            MODE_F32 => self.format.replace(r#""%""#, &y.to_string()),
            MODE_I32 => self.format.replace(r#""%""#, &(y as i32).to_string()),
            MODE_PITCH_WHEEL => {
                let y = y as i32;
                let y = {
                    if y > 0x3fff {
                        0x3fff
                    } else if y < 0 {
                        0
                    } else {
                        y
                    }
                };
                self.format
                    .replace(r#""%l""#, &(y & 0x7f).to_string())
                    .replace(r#""%h""#, &(y >> 7).to_string())
            }
            _ => return,
        };
        if let Ok(body) = serde_json::from_str(&text) {
            for output in &self.outputs {
                if let Some(result) = output.command(&body) {
                    if let Some(error) = result.get("error") {
                        self.last_error = error.as_str().unwrap_or(&error.to_string()).into();
                    }
                }
            }
        }
        for i in &mut self.cv {
            *i = 0.0;
        }
    }

    fn audio(&mut self) -> Option<&mut [f32]> {
        Some(self.cv.as_mut_slice())
    }
}
