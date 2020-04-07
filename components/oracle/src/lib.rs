use dlal_component_base::{
    arg, arg_num, arg_str, command, gen_component, join, json, json_from_str, json_get, json_num,
    json_str, kwarg_num, multi, View,
};

use std::vec::Vec;

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
}

gen_component!(Specifics);

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
                    .resize(kwarg_num(&body, "samples_per_evaluation")?, 0.0);
                Ok(None)
            },
            ["samples_per_evaluation"],
        );
        multi!(connect commands, false);
        command!(
            commands,
            "format",
            |soul, body| {
                soul.format = arg_str(&body, 0)?.to_string();
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
                soul.mode = arg_num(&body, 0)?;
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
                soul.m = arg_num(&body, 0)?;
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
                soul.b = arg_num(&body, 0)?;
                Ok(Some(json!(soul.b)))
            },
            {
                "args": ["b"],
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
                let j = arg(&body, 0)?;
                soul.m = json_num(json_get(j, "m")?)?;
                soul.b = json_num(json_get(j, "b")?)?;
                soul.mode = json_num(json_get(j, "mode")?)?;
                soul.format = json_str(json_get(j, "format")?)?.to_string();
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        let y = self.m * self.cv[0] + self.b;
        let text = match self.mode {
            MODE_F32 => self.format.replace("%", &y.to_string()),
            MODE_I32 => self.format.replace("%", &(y as i32).to_string()),
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
                    .replace("%l", &(y & 0x7f).to_string())
                    .replace("%h", &(y >> 7).to_string())
            }
            _ => return,
        };
        if let Ok(body) = json_from_str(&text) {
            for output in &self.outputs {
                output.command(&body);
            }
        }
    }

    fn audio(&mut self) -> Option<&mut [f32]> {
        Some(self.cv.as_mut_slice())
    }
}
