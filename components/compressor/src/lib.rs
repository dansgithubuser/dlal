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
                "peak_smooth_rise",
                "peak_smooth_fall",
                "gain_smooth_rise",
                "gain_smooth_fall",
                "max_gain",
                "volume"
            ],
            "kinds": ["rw", "json"]
        },
        {
            "name": "field_helpers",
            "fields": [
                "peak",
                "peak_smoothed",
                "gain"
            ],
            "kinds": ["r"]
        },
    ],
    {
        peak: f32, // peak (absolute)
        peak_smoothed: f32,
        gain: f32,
        peak_smooth_rise: f32,
        peak_smooth_fall: f32,
        gain_smooth_rise: f32,
        gain_smooth_fall: f32,
        max_gain: f32,
        volume: f32,
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.peak_smooth_rise = 0.95;
        self.peak_smooth_fall = 0.999;
        self.gain_smooth_rise = 0.9995;
        self.gain_smooth_fall = 0.9;
        self.max_gain = 50.0;
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
            macro_rules! smooth {
                ($smoothed:expr, $raw:expr, $smooth_rise:expr, $smooth_fall:expr) => {
                    let smooth = if $smoothed < $raw {
                        $smooth_rise
                    } else {
                        $smooth_fall
                    };
                    $smoothed = smooth * $smoothed + (1.0 - smooth) * $raw;
                }
            }
            let peak = peak.max(self.peak);
            smooth!(self.peak_smoothed, peak, self.peak_smooth_rise, self.peak_smooth_fall);
            let peak = peak.max(self.peak_smoothed);
            let mut gain_f = 1.0 / (peak + 1.0 / self.max_gain);
            if peak < 1.0 / self.max_gain {
                gain_f *= peak * self.max_gain;
            }
            smooth!(self.gain, gain_f, self.gain_smooth_rise, self.gain_smooth_fall);
            *i *= self.gain * self.volume;
        }
        self.peak = peak;
    }
}
