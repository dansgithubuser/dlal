use serde_json::json;

use proc_macro::{TokenStream, TokenTree};

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

fn get_features(input: TokenStream) -> serde_json::Value {
    let tokens = stream_to_vec(input);
    let mut result = json!({});
    let mut field_helpers_all = Vec::<String>::new();
    let mut field_helpers_rw = Vec::<String>::new();
    let mut field_helpers_r = Vec::<String>::new();
    let mut field_helpers_json = Vec::<String>::new();
    for i in (0..tokens.len()).step_by(2) {
        let features = serde_json::from_str::<serde_json::Value>(&tokens[i].to_string())
            .expect("feature isn't valid JSON");
        match features {
            serde_json::Value::String(name) => {
                result[name] = json!(true);
            }
            serde_json::Value::Object(mut feature) => {
                let name = String::from(feature["name"].as_str().expect("bad feature name"));
                match name.as_str() {
                    "join_info" | "connect_info" | "disconnect_info" => {
                        feature.remove("name");
                        result[name] = json!(json!(feature).to_string());
                    }
                    "field_helpers" => {
                        let fields = feature["fields"].as_array().expect("fields isn't an array");
                        for field in fields {
                            let field = field.as_str().expect("field isn't a string");
                            field_helpers_all.push(field.to_string());
                            let kinds = feature["kinds"].as_array().expect("kinds isn't an array");
                            for kind in kinds {
                                let kind = kind.as_str().expect("kind isn't a string");
                                match kind {
                                    "rw" => field_helpers_rw.push(field.to_string()),
                                    "r" => field_helpers_r.push(field.to_string()),
                                    "json" => field_helpers_json.push(field.to_string()),
                                    _ => panic!("unknown field helper kind {}", kind),
                                }
                            }
                        }
                    }
                    _ => {
                        panic!("unknown complex feature \"{}\"", feature["name"]);
                    }
                }
            }
            _ => panic!("invalid feature type"),
        }
    }
    result["field_helpers"] = json!({
        "all": field_helpers_all,
        "rw": field_helpers_rw,
        "r": field_helpers_r,
        "json": field_helpers_json,
    });
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
    // read configuration
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
    let mut commands = get_commands(inside(&tts[6]));
    // processing
    {
        let field_helpers = features.get("field_helpers").expect("missing field_helpers");
        let command_names = commands
            .iter()
            .map(|i| i["name"].as_str().expect("command has no name").to_string())
            .collect::<Vec<_>>();
        let rw = field_helpers["rw"].as_array().expect("field_helpers.rw isn't an array");
        for field in rw {
            let field = field.as_str().expect("field_helpers.rw[_] isn't a string").to_string();
            if command_names.contains(&field) {
                continue;
            }
            let info = json!({
                "args": [{"name": field, "optional": true}],
                "return": field,
            });
            commands.push(json!({
                "name": field,
                "info": info.to_string(),
            }));
        }
        let r = field_helpers["r"].as_array().expect("field_helpers.r isn't an array");
        for field in r {
            let field = field.as_str().expect("field_helpers.r[_] isn't a string").to_string();
            if command_names.contains(&field) {
                continue;
            }
            let info = json!({
                "return": field,
            });
            commands.push(json!({
                "name": field,
                "info": info.to_string(),
            }));
        }
    }
    // render
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
        .expect("render failed");
    if let Ok(path) = std::env::var("DLAL_COMPONENT_MACRO_RENDER_PATH") {
        let path = format!("{}/component.hbs.render.rs", path);
        println!("writing dlal-component-macro output to {}", path);
        std::fs::write(path, &render).expect("write failed");
    }
    render.parse().expect("parse failed")
}
