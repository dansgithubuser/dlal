use dlal_component_base::component;

use std::iter::zip;

component!(
    {"in": ["audio"], "out": ["audio"]},
    [
        "run_size",
        "uni",
        "audio",
        "check_audio",
        {"name": "field_helpers", "fields": ["decay", "e"], "kinds": ["rw", "json"]},
    ],
    {
        value: f32,
        decay: f32,
        e: f32,
    },
    {},
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.decay = 0.999;
        self.e = 0.01;
    }

    fn run(&mut self) {
        let y = match &self.output {
            Some(output) => output.audio(self.run_size).unwrap(),
            None => return,
        };
        for (i, j) in zip(&self.audio, y) {
            self.value *= self.decay;
            if self.value < i.abs() {
                self.value = i.abs();
            }
            if self.value > self.e {
                *j *= i / self.value;
            }
        }
        for i in &mut self.audio {
            *i = 0.0;
        }
    }
}
