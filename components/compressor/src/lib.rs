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
                "gain_min",
                "gain_max",
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
        gain_min: f32,
        gain_max: f32,
        volume: f32,
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.gain = 1.0;
        self.peak_smooth_rise = 0.95;
        self.peak_smooth_fall = 0.999;
        self.gain_smooth_rise = 0.9995;
        self.gain_smooth_fall = 0.95;
        self.gain_min = 1.0;
        self.gain_max = 40.0;
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
            let gain_f = if 1.0 > self.gain_max * peak {
                // too quiet
                // if 1 / peak is near gain_max, we want gain_f = gain_max
                // in this case, gain_max * peak is near 1
                // if 1 / peak is far greater than gain_max, we want gain_f = gain_min
                // in this case, peak is near 0 and gain_max * peak is near 0
                let t = self.gain_max * peak;
                (self.gain_max * t).max(self.gain_min)
            } else if 1.0 < self.gain_min * peak {
                // too loud - have gain approach gain_min
                self.gain_min
            } else {
                // typical case - have gain approach 1 / peak for consistent volume
                1.0 / peak
            };
            smooth!(self.gain, gain_f, self.gain_smooth_rise, self.gain_smooth_fall);
            *i *= self.gain * self.volume;
        }
        self.peak = peak;
    }
}
