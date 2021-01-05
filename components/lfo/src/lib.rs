use dlal_component_base::component;

use std::f32::consts::PI;

component!(
    {"in": [], "out": ["audio"]},
    [
        "run_size",
        "sample_rate",
        "uni",
        "check_audio",
        {"name": "field_helpers", "fields": ["freq", "amp"], "kinds": ["rw", "json"]},
    ],
    {
        freq: f32,
        amp: f32,
        phase: f32,
    },
    {},
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.freq = 1.0;
        self.amp = 0.1;
    }

    fn run(&mut self) {
        let step = 2.0 * PI * self.freq / self.sample_rate as f32;
        if let Some(output) = self.output.as_ref() {
            let audio = output.audio(self.run_size).unwrap();
            for i in 0..self.run_size {
                audio[i] += self.amp * self.phase.sin();
                self.phase += step;
            }
        } else {
            self.phase += step * self.run_size as f32;
        }
        if self.phase > 2.0 * PI {
            self.phase -= 2.0 * PI;
        }
    }
}
