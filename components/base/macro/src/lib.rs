use serde_json::json;

use proc_macro::{TokenStream, TokenTree};
use std::collections::HashMap;

fn stream_to_vec(input: TokenStream) -> Vec<TokenTree> {
    input.into_iter().collect::<Vec<_>>()
}

fn inside(tt: &TokenTree) -> TokenStream {
    let group = match tt {
        TokenTree::Group(group) => group,
        _ => panic!("expected a group, found {}", tt),
    };
    group.stream()
}

fn get_features(input: TokenStream) -> HashMap<String, String> {
    let tokens = stream_to_vec(input);
    let mut result = HashMap::<String, String>::new();
    for i in (0..tokens.len()).step_by(2) {
        let features = serde_json::from_str::<serde_json::Value>(&tokens[i].to_string())
            .expect("feature isn't valid JSON");
        match features {
            serde_json::Value::String(name) => {
                result.insert(name, "true".into());
            }
            serde_json::Value::Object(feature) => {
                result.insert(
                    feature["name"]
                        .as_str()
                        .expect("feature name isn't a string")
                        .into(),
                    feature["value"].to_string(),
                );
            }
            _ => panic!("invalid feature type"),
        }
    }
    result
}

fn get_commands(input: TokenStream) -> Vec<serde_json::Value> {
    let tokens = stream_to_vec(input);
    let mut result = vec![];
    for i in (0..tokens.len()).step_by(4) {
        result.push(json!({
            "name": tokens[i].to_string().replace("\"", ""),
            "info": tokens[i + 2].to_string(),
        }));
    }
    result
}

#[proc_macro]
pub fn component(input: TokenStream) -> TokenStream {
    let tts = stream_to_vec(input);
    let info = &tts[0];
    if tts[1].to_string() != "," {
        panic!("missing a comma after info");
    }
    let features = get_features(inside(&tts[2]));
    if tts[3].to_string() != "," {
        panic!("missing a comma after features");
    }
    let fields = inside(&tts[4]);
    if tts[5].to_string() != "," {
        panic!("missing a comma after fields");
    }
    let commands = get_commands(inside(&tts[6]));
    let mut hbs = handlebars::Handlebars::new();
    hbs.register_escape_fn(handlebars::no_escape);
    let render = hbs
        .render_template(
            include_str!("../component.hbs.rs"),
            &json!({
                "info": info.to_string(),
                "features": features,
                "fields": fields.to_string(),
                "commands": commands,
            }),
        )
        .unwrap();
    if let Ok(path) = std::env::var("DLAL_COMPONENT_MACRO_RENDER_PATH") {
        let path = format!("{}/component.hbs.render.rs", path);
        println!("writing dlal-component-macro output to {}", path);
        std::fs::write(path, &render).unwrap();
    }
    render.parse().unwrap()
}
