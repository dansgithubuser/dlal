use dlal_component_base::component;

component!(
    {"in": ["audio"], "out": ["audio"]},
    [
        {"name": "join_info", "kwargs": ["run_size"]},
        "multi",
        "audio",
        "check_audio",
        {"name": "field_helpers", "fields": ["value"], "kinds": ["r"]},
    ],
    {
        value: f32,
    },
    {},
);

impl ComponentTrait for Component {
    fn run(&mut self) {
        for i in &mut self.audio {
            self.value *= 0.999;
            if self.value < i.abs() {
                self.value = i.abs();
            }
            *i = self.value;
        }
        self.multi_audio(&self.audio);
        for i in &mut self.audio {
            *i = 0.0;
        }
    }
}
