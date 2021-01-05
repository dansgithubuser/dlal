use dlal_component_base::{component, err, json, serde_json, Arg, Body, CmdResult};

use lazy_static::lazy_static;
use regex::Regex;
use serde::{Deserialize, Serialize};

lazy_static! {
    static ref RE: Regex = Regex::new(concat!(
        r#"""#,
        r"%(\d+)",
        r"(?:\*([\d.e-]+))?",
        r"(?:\+([\d.e-]+))?",
        r#"""#,
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
                if std::option_env!("DLAL_SNOOP_MIDMAN").is_some() {
                    println!("no match, pattern longer than {:02x?}", msg);
                }
                break;
            }
            match self.pattern[i] {
                Piece::Byte(b) => {
                    if b != msg[i] {
                        if std::option_env!("DLAL_SNOOP_MIDMAN").is_some() {
                            println!("no match, piece {} (byte), msg {:02x?}", i, msg);
                        }
                        return false;
                    }
                }
                Piece::Null => (),
                Piece::LeastSignificantNibble(b) => {
                    if b != msg[i] & 0xf {
                        if std::option_env!("DLAL_SNOOP_MIDMAN").is_some() {
                            println!("no match, piece {} (little nibble), msg {:02x?}", i, msg);
                        }
                        return false;
                    }
                }
                Piece::MostSignificantNibble(b) => {
                    if b != msg[i] & 0xf0 {
                        if std::option_env!("DLAL_SNOOP_MIDMAN").is_some() {
                            println!("no match, piece {} (big nibble), msg {:02x?}", i, msg);
                        }
                        return false;
                    }
                }
            }
        }
        true
    }

    fn sub(&self, msg: &[u8]) -> serde_json::Value {
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
        match serde_json::from_str(text) {
            Ok(body) => body,
            Err(_) => json!("null"),
        }
    }
}

component!(
    {"in": ["midi"], "out": ["cmd"]},
    [
        "multi",
        {"name": "field_helpers", "fields": ["last_error"], "kinds": ["r"]},
    ],
    {
        directives: Vec<Directive>,
        last_error: String,
    },
    {
        "directive": {
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
    },
);

impl ComponentTrait for Component {
    fn midi(&mut self, msg: &[u8]) {
        for directive in &self.directives {
            if directive.matches(msg) {
                if directive.component >= self.outputs.len() {
                    if std::option_env!("DLAL_SNOOP_MIDMAN").is_some() {
                        println!("component index {} out of range", directive.component);
                    }
                    continue;
                }
                if let Some(result) = self.outputs[directive.component].command(&directive.sub(msg))
                {
                    if let Some(error) = result.get("error") {
                        self.last_error = error.as_str().unwrap_or(&error.to_string()).into();
                        if std::option_env!("DLAL_SNOOP_MIDMAN").is_some() {
                            println!("command error: {}", self.last_error);
                        }
                    }
                }
            }
        }
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({
            "directives": self.directives,
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = body.arg::<serde_json::Value>(0)?;
        self.directives =
            serde_json::from_str(&j.at::<serde_json::Value>("directives")?.to_string())?;
        Ok(None)
    }
}

impl Component {
    fn directive_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let pattern = body.arg::<Vec<_>>(0)?.vec_map(|i| match i {
            serde_json::Value::Null => Ok(Piece::Null),
            serde_json::Value::Number(_) => Ok(Piece::Byte(i.to()?)),
            serde_json::Value::Object(map) => {
                if let Some(nibble) = map.get("nibble") {
                    let nibble: u8 = nibble.to()?;
                    if nibble >= 0x10 {
                        if nibble & 0xf != 0 {
                            return Err(err!("expected one nibble to be 0").into());
                        }
                        Ok(Piece::MostSignificantNibble(nibble))
                    } else {
                        Ok(Piece::LeastSignificantNibble(nibble))
                    }
                } else {
                    Err(err!("unknown pattern object").into())
                }
            }
            v => Err(err!("pattern element {:?} is invalid", v).into()),
        })?;
        self.directives.push(Directive {
            pattern,
            component: body.arg(1)?,
            format: body.arg(2)?,
        });
        Ok(None)
    }
}
