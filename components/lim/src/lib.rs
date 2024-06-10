use dlal_component_base::component;

component!(
    {"in": [], "out": ["audio"]},
    [
        "run_size",
        "multi",
        "check_audio",
        {"name": "field_helpers", "fields": ["soft", "soft_gain", "hard"], "kinds": ["rw", "json"]},
    ],
    {
        soft: f32,
        soft_gain: f32,
        hard: f32,
    },
    {
        "soft": {
            "args": [{
                "name": "soft",
                "optional": true,
                "default": 1.0,
            }],
        },
        "soft_gain": {
            "args": [{
                "name": "soft_gain",
                "optional": true,
                "default": 0.5,
            }],
        },
        "hard": {
            "args": [{
                "name": "hard",
                "optional": true,
                "default": 1.0,
            }],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.soft = 1.0;
        self.soft_gain = 0.5;
        self.hard = 1.0;
    }

    fn run(&mut self) {
        for output in &self.outputs {
            let audio = output.audio(self.run_size).unwrap();
            for i in audio {
                if *i > self.soft {
                    *i = self.soft + (*i - self.soft) * self.soft_gain;
                    if *i > self.hard {
                        *i = self.hard;
                    }
                } else if *i < -self.soft {
                    *i = -self.soft + (*i + self.soft) * self.soft_gain;
                    if *i < -self.hard {
                        *i = -self.hard;
                    }
                }
                //let over = i.abs() - self.soft;
                //if over > 0.0 {
                //    let y = self.soft + (self.hard - self.soft) * (1.0 - 1.0 / (over + 1.0));
                //    if *i > 0.0 {
                //        *i = y;
                //    } else {
                //        *i = -y;
                //    }
                //}
            }
        }
    }
}
