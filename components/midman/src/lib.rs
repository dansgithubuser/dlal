use dlal_component_base::{
    command, err, gen_component, json, json_from_str, marg, multi, JsonValue, View,
};

use lazy_static::lazy_static;
use regex::Regex;
use serde::{Deserialize, Serialize};

use std::vec::Vec;

lazy_static! {
    static ref RE: Regex = Regex::new(concat!(
        r"%(\d+)",
        r"(?:\*([\d.e-]+))?",
        r"(?:\+([\d.e-]+))?",
    ))
    .unwrap();
}

#[derive(Serialize, Deserialize)]
enum Piece {
    Byte(u8),
    Null,
    LeastSignificantNibble(u8),
    MostSignificantNibble(u8),
}

#[derive(Serialize, Deserialize)]
struct Directive {
    pattern: Vec<Piece>,
    component: usize,
    format: String,
}

impl Directive {
    fn matches(&self, msg: &[u8]) -> bool {
        for i in 0..self.pattern.len() {
            if i > msg.len() {
                break;
            }
            match self.pattern[i] {
                Piece::Byte(b) => {
                    if b != msg[i] {
                        return false;
                    }
                }
                Piece::Null => (),
                Piece::LeastSignificantNibble(b) => {
                    if b != msg[i] & 0xf {
                        return false;
                    }
                }
                Piece::MostSignificantNibble(b) => {
                    if b != msg[i] & 0xf0 {
                        return false;
                    }
                }
            }
        }
        true
    }

    fn sub(&self, msg: &[u8]) -> JsonValue {
        let text = &RE
            .replace_all(&self.format, |captures: &regex::Captures| -> String {
                let i = match captures.get(1) {
                    Some(i) => i,
                    None => return "null".into(),
                };
                let i = match i.as_str().parse::<usize>() {
                    Ok(i) => i,
                    Err(_) => return "null".into(),
                };
                let m = match captures.get(2) {
                    Some(m) => match m.as_str().parse::<f32>() {
                        Ok(m) => m,
                        Err(_) => return "null".into(),
                    },
                    None => 1.0,
                };
                let b = match captures.get(3) {
                    Some(b) => match b.as_str().parse::<f32>() {
                        Ok(b) => b,
                        Err(_) => return "null".into(),
                    },
                    None => 0.0,
                };
                if i >= msg.len() {
                    return "null".into();
                }
                (msg[i] as f32 * m + b).to_string()
            })
            .to_string();
        match json_from_str(text) {
            Ok(body) => body,
            Err(_) => json!("null"),
        }
    }
}

#[derive(Default)]
pub struct Specifics {
    directives: Vec<Directive>,
    outputs: Vec<View>,
    last_error: String,
}

gen_component!(Specifics, {"in": ["midi"], "out": ["cmd"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            ..Default::default()
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        multi!(connect commands, false);
        command!(
            commands,
            "directive",
            |soul, body| {
                let pattern = marg!(arg &body, 0)?
                    .as_array()
                    .ok_or_else(|| err!(box "pattern isn't an array"))?
                    .iter()
                    .map(|i| {
                        match i {
                            JsonValue::Null => Ok(Piece::Null),
                            JsonValue::String(_) => {
                                Ok(Piece::Byte(marg!(json_num &i)?))
                            },
                            JsonValue::Object(map) => {
                                if let Some(nibble) = map.get("nibble") {
                                    let nibble = marg!(json_num &nibble)?;
                                    if nibble >= 0x10 {
                                        if nibble & 0xf != 0 {
                                            return err!("expected one nibble to be 0");
                                        }
                                        Ok(Piece::MostSignificantNibble(nibble))
                                    }
                                    else {
                                        Ok(Piece::LeastSignificantNibble(nibble))
                                    }
                                } else {
                                    err!("unknown pattern object")
                                }
                            },
                            _ => err!("pattern element type is invalid"),
                        }
                    })
                    .collect::<Result<_, _>>()?;
                soul.directives.push(Directive {
                    pattern,
                    component: marg!(arg_num &body, 1)?,
                    format: marg!(arg_str &body, 2)?.into(),
                });
                Ok(None)
            },
            {
                "args": [
                    {
                        "name": "pattern",
                        "type": "array",
                        "element": {
                            "choices": [
                                {
                                    "name": "byte",
                                    "desc": "match equal",
                                },
                                {
                                    "name": "null",
                                    "desc": "match anything",
                                },
                                {
                                    "name": "object",
                                    "values": {
                                        "nibble": "nibble",
                                    },
                                    "desc": "match based on provided values",
                                },
                            ],
                        },
                    },
                    {
                        "name": "component",
                        "type": "unsigned",
                        "desc": "index into connected components to send the command to",
                    },
                    {
                        "name": "format",
                        "type": "string",
                        "desc": "command text to have MIDI bytes subbed in; %1*2+3 becomes MIDI byte 1 multiplied by 2 plus 3"
                    },
                ],
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
                    "directives": soul.directives,
                })))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                let j = marg!(arg &body, 0)?;
                soul.directives = json_from_str(&marg!(json_get j, "directives")?.to_string())?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn midi(&mut self, msg: &[u8]) {
        for directive in &self.directives {
            if directive.matches(msg) {
                if directive.component >= self.outputs.len() {
                    continue;
                }
                if let Some(result) = self.outputs[directive.component].command(&directive.sub(msg)) {
                    if let Some(error) = result.get("error") {
                        self.last_error = error.as_str().unwrap_or(&error.to_string()).into();
                    }
                }
            }
        }
    }
}
