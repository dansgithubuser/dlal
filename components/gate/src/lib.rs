use dlal_component_base::component;

component!(
    {"in": [], "out": ["audio"]},
    [
        "run_size",
        "uni",
        "check_audio",
        {
            "name": "field_helpers",
            "fields": ["threshold", "smooth"], "kinds": ["rw", "json"]
        },
        {
            "name": "field_helpers",
            "fields": ["gain"], "kinds": ["r"]
        },
    ],
    {
        threshold: f32,
        smooth: f32,
        gain: f32,
    },
    {
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.threshold = 0.0;
        self.smooth = 0.999;
        self.gain = 1.0;
    }

    fn run(&mut self) {
        let y = match &self.output {
            Some(output) => output.audio(self.run_size).unwrap(),
            None => return,
        };
        let mut peak: f32 = 0.0;
        for i in &*y {
            peak = peak.max(i.abs());
        }
        let gain_f = if peak < self.threshold {
            0.0
        } else {
            1.0
        };
        for i in y {
            self.gain = self.smooth * self.gain + (1.0 - self.smooth) * gain_f;
            *i *= self.gain;
        }
    }
}
