use dlal_component_base::component;

use std::collections::VecDeque;

component!(
    {"in": [""], "out": ["audio"]},
    [
        "run_size",
        "uni",
        "check_audio",
        {"name": "field_helpers", "fields": ["cents"], "kinds": ["rw", "json"]},
    ],
    {
        cents: f32,
        offset: f32,
        buffer: VecDeque<f32>,
    },
    {
    },
);

impl ComponentTrait for Component {
    fn run(&mut self) {
        let audio = match &mut self.output {
            Some(output) => output.audio(self.run_size).unwrap(),
            None => return,
        };
        for i in audio {
            self.buffer.push_back(*i);
            if self.buffer.len() <= 2 {
                continue;
            }
            self.offset += 2.0_f32.powf(-self.cents / 100.0 / 12.0);
            if self.offset >= 1.0 {
                self.offset -= 1.0;
                self.buffer.pop_front();
            }
            *i = (1.0 - self.offset) * self.buffer[0] + self.offset * self.buffer[1];
        }
    }
}
