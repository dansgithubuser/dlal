use dlal_component_base::{component, serde_json, Body, CmdResult};

const MODE_F32: u8 = 0;
const MODE_I32: u8 = 1;
const MODE_PITCH_WHEEL: u8 = 2;

component!(
    {"in": ["audio"], "out": ["cmd", "midi"]},
    [
        "multi",
        {"name": "join_info", "kwargs": ["run_size"]},
        {"name": "field_helpers", "fields": ["format", "mode", "m", "b", "cv_i"], "kinds": ["rw", "json"]},
        {"name": "field_helpers", "fields": ["last_error"], "kinds": ["r"]},
    ],
    {
        cv: Vec<f32>,
        cv_i: f32,
        m: f32,
        b: f32,
        mode: u8,
        format: String,
        last_error: String,
    },
    {
        "format": {"args": ["format"]},
        "mode": {"args": [{"name": "mode", "default": "f32"}]},
        "m": {"args": [{"name": "m", "default": 1}]},
        "b": {"args": [{"name": "b", "default": 0}]},
        "cv_i": {"args": [{"name": "cv_i", "default": 0}]},
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
            *i = self.cv_i;
        }
    }

    fn audio(&mut self) -> Option<&mut [f32]> {
        Some(self.cv.as_mut_slice())
    }
}
