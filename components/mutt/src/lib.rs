use dlal_component_base::component;

use std::iter::zip;

component!(
    {"in": ["audio"], "out": ["audio"]},
    [
        "run_size",
        "sample_rate",
        "uni",
        "audio",
        "check_audio",
        {"name": "field_helpers", "fields": ["smooth_rise", "smooth_fall", "e"], "kinds": ["rw", "json"]},
        {"name": "field_helpers", "fields": ["value", "peak"], "kinds": ["r"]},
    ],
    {
        value: f32, // follows contour of modulator
        peak: f32, // modulator peak (absolute)
        smooth_rise: f32, // how smooth value is when below peak
        smooth_fall: f32, // how smooth value is when above peak
        e: f32, // only when value is greater than this should output signal be multiplied by input signal
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.smooth_rise = 0.95;
        self.smooth_fall = 0.999;
        self.e = 0.2;
    }

    fn run(&mut self) {
        let y = match &self.output {
            Some(output) => output.audio(self.run_size).unwrap(),
            None => return,
        };
        let mut peak = 0.0;
        for (i, j) in zip(&self.audio, y) {
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
            if self.value > self.e {
                *j *= i / self.value;
            }
        }
        self.peak = peak;
        for i in &mut self.audio {
            *i = 0.0;
        }
    }
}
