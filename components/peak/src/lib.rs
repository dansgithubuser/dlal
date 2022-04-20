use dlal_component_base::component;

component!(
    {"in": ["audio"], "out": ["audio"]},
    [
        {"name": "join_info", "kwargs": ["run_size"]},
        "multi",
        "audio",
        "check_audio",
        {"name": "field_helpers", "fields": ["value"], "kinds": ["r"]},
        {"name": "field_helpers", "fields": ["decay"], "kinds": ["rw", "json"]},
    ],
    {
        value: f32,
        decay: f32,
    },
    {},
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.decay = 0.999;
    }

    fn run(&mut self) {
        for i in &mut self.audio {
            self.value *= self.decay;
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
