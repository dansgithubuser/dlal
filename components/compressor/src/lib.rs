use dlal_component_base::component;

component!(
    {"in": [], "out": ["audio"]},
    [
        "run_size",
        "uni",
        "check_audio",
        {
            "name": "field_helpers",
            "fields": [
                "smooth_rise",
                "smooth_fall",
                "lo",
                "hi",
                "volume"
            ],
            "kinds": ["rw", "json"]
        },
        {"name": "field_helpers", "fields": ["value", "peak"], "kinds": ["r"]},
    ],
    {
        value: f32, // follows contour of audio
        peak: f32, // peak (absolute)
        smooth_rise: f32, // how smooth value is when below peak
        smooth_fall: f32, // how smooth value is when above peak
        lo: f32, // anything quieter than this is silenced
        hi: f32, // anything louder than this is made to have specified volume (so there's a smooth region between lo and hi)
        volume: f32,
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.smooth_rise = 0.95;
        self.smooth_fall = 0.999;
        self.lo = 0.001;
        self.hi = 0.01;
        self.volume = 0.5;
    }

    fn run(&mut self) {
        let y = match &self.output {
            Some(output) => output.audio(self.run_size).unwrap(),
            None => return,
        };
        let mut peak = 0.0;
        for i in y {
            let mag = i.abs();
            if peak < mag {
                peak = mag;
            }
            let smooth = if self.value < self.peak {
                self.smooth_rise
            } else {
                self.smooth_fall
            };
            self.value = smooth * self.value + (1.0 - smooth) * self.peak;
            if self.value < self.lo {
                *i = 0.0;
            } else if self.value > self.hi {
                *i *= self.volume / self.value;
            } else {
                let t = (self.value - self.lo) / (self.hi - self.lo);
                *i *= t * self.volume / self.value;
            }
        }
        self.peak = peak;
    }
}
