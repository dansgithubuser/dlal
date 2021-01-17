use dlal_component_base::component;

component!(
    {"in": ["midi"], "out": ["midi"]},
    [
        "uni",
        {"name": "field_helpers", "fields": ["gain"], "kinds": ["rw", "json"]},
    ],
    {
        gain: f32,
    },
    {
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.gain = 1.0;
    }

    fn midi(&mut self, msg: &[u8]) {
        if msg.len() >= 3 && msg[0] & 0xe0 == 0x80 {
            let mut v = self.gain * msg[2] as f32;
            if v > 127.0 {
                v = 127.0;
            }
            self.uni_midi(&[msg[0], msg[1], v as u8]);
        } else {
            self.uni_midi(msg);
        };
    }
}
