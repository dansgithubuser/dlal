use dlal_component_base::{component, json_to_ptr, serde_json, Body, CmdResult};

component!(
    {"in": ["cmd"], "out": []},
    [
        "run_size",
        "sample_rate",
        {
            "name": "field_helpers",
            "fields": [
                "register_count",
                "register_distance_factor",
                "register_width_factor",
                "smoothness"
            ],
            "kinds": ["rw", "json"]
        },
    ],
    {
        registers: Vec<f32>,
        register_count: usize,
        register_distance_factor: f32,
        register_width_factor: f32,
        smoothness: f32,
    },
    {
        "stft": {
            "args": [{
                "name": "stft",
                "kind": "norm",
            }],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.register_count = 30;
        self.register_distance_factor = 1.2;
        self.register_width_factor = 1.5;
        self.smoothness = 0.9;
    }
}

impl Component {
    fn stft_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let data = json_to_ptr!(body.arg::<serde_json::Value>(0)?, *const f32);
        let len = body.arg(1)?;
        let stft = unsafe { std::slice::from_raw_parts(data, len) };
        if self.register_count != self.registers.len() {
            self.registers.resize(self.register_count, 0.0);
        }
        let mut freq_max = self.sample_rate as f32 / 2.0;
        for i in (0..self.registers.len()).rev() {
            let freq_min = freq_max / self.register_width_factor;
            let s = stft.len() as f32 / self.sample_rate as f32;
            let a = (s * freq_min) as usize;
            let b = (s * freq_max) as usize;
            let v = stft[a..b].iter().sum::<f32>().log(10.0);
            self.registers[i] = self.smoothness * self.registers[i] + (1.0 - self.smoothness) * v;
            freq_max /= self.register_distance_factor;
            print!("{:.1} ", self.registers[i]);
        }
        println!("");
        Ok(None)
    }
}
