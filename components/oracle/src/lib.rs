use dlal_component_base::{component, json, serde_json, Body, CmdResult};

const MODE_F32: u8 = 0;
const MODE_I32: u8 = 1;
const MODE_PITCH_WHEEL: u8 = 2;

component!(
    {"in": ["audio"], "out": ["cmd", "midi"]},
    [
        "multi",
        {"name": "join_info", "value": {"kwargs": ["run_size"]}},
    ],
    {
        cv: Vec<f32>,
        m: f32,
        b: f32,
        mode: u8,
        format: String,
        last_error: String,
    },
    {
        "format": {"args": ["format"]},
        "mode": {"args": ["mode"]},
        "m": {"args": ["m"]},
        "b": {"args": ["b"]},
        "last_error": {},
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.m = 1.0;
    }

    fn join(&mut self, body: serde_json::Value) -> CmdResult {
        self.cv.resize(body.kwarg("run_size")?, 0.0);
        Ok(None)
    }

    fn run(&mut self) {
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

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({
            "m": self.m,
            "b": self.b,
            "mode": self.mode,
            "format": self.format,
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = body.arg::<serde_json::Value>(0)?;
        self.m = j.at("m")?;
        self.b = j.at("b")?;
        self.mode = j.at("mode")?;
        self.format = j.at("format")?;
        Ok(None)
    }
}

impl Component {
    fn format_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.format = body.arg(0)?;
        Ok(Some(json!(self.format)))
    }

    fn mode_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.mode = body.arg(0)?;
        Ok(Some(json!(self.mode)))
    }

    fn m_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.m = body.arg(0)?;
        Ok(Some(json!(self.m)))
    }

    fn b_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.b = body.arg(0)?;
        Ok(Some(json!(self.b)))
    }
    fn last_error_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!(self.last_error)))
    }
}
