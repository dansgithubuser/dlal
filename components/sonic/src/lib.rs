use dlal_component_base::{gen_component, json, View, VIEW_ARGS};

pub struct Specifics {
    views: Vec<View>,
}

gen_component!(Specifics);

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Specifics {
            views: vec![],
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        commands.insert(
            "connect",
            Command {
                func: |soul, body| {
                    Ok(None)
                },
                info: json!({
                    "args": VIEW_ARGS,
                }),
            },
        );
    }

    fn midi(&mut self, msg: &[u8]) {
        println!("sonic got MIDI msg: {:?}", msg);
    }

    fn evaluate(&mut self) {}
}
