use dlal_component_base::component;

component!(
    {"in": [], "out": ["audio"]},
    [
        "run_size",
        "multi",
        "check_audio",
        {"name": "field_helpers", "fields": ["c"], "kinds": ["rw", "json"]},
    ],
    {
        c: f32,
    },
    {
        "c": {
            "args": [{"name": "c", "optional": true}],
        },
    },
);

impl ComponentTrait for Component {
    fn run(&mut self) {
        if self.outputs.is_empty() {
            return;
        }
        for i in 0..(self.outputs.len() - 1) {
            let x = self.outputs[i + 0].audio(self.run_size).unwrap();
            let y = self.outputs[i + 1].audio(self.run_size).unwrap();
            for j in 0..self.run_size {
                y[j] *= x[j] + self.c;
            }
        }
    }
}
