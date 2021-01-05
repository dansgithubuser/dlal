use dlal_component_base::component;

component!(
    {"in": [], "out": ["audio"]},
    [
        "run_size",
        "multi",
        "check_audio",
        {"name": "field_helpers", "fields": ["mode"], "kinds": ["rw", "json"]},
    ],
    {
        mode: String,
    },
    {
        "mode": {
            "args": [{
                "name": "mode",
                "optional": true,
                "choices": ["exp2", "sqrt"],
            }],
        },
    },
);

impl ComponentTrait for Component {
    fn run(&mut self) {
        for output in &self.outputs {
            for i in output.audio(self.run_size).unwrap() {
                *i = match self.mode.as_str() {
                    "exp2" => i.exp2(),
                    "sqrt" => {
                        if *i >= 0.0 {
                            i.sqrt()
                        } else {
                            -(-*i).sqrt()
                        }
                    }
                    _ => *i,
                }
            }
        }
    }
}
