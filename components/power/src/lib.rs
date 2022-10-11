use dlal_component_base::{component, json, serde_json, CmdResult};

component!(
    {"in": ["audio"], "out": []},
    [
        "audio",
    ],
    {
        x: f32,
        energies: Vec<f32>,
        index: usize,
    },
    {
        power: {"args": []},
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.x = 0.0;
        self.energies.resize(8, 0.0);
        self.index = 0;
    }

    fn run(&mut self) {
        let mut energy: f32 = 0.0;
        for x in &mut self.audio {
            let d = *x - self.x; // get air velocity -- displacement does not make energy
            energy += d * d;
            self.x = *x;
            *x = 0.0;
        }
        self.energies[self.index] = energy;
        self.index += 1;
        self.index %= self.energies.len();
    }
}

impl Component {
    fn power_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        let power = self.energies.iter().sum::<f32>() / (self.energies.len() * self.run_size) as f32;
        Ok(Some(json!(power)))
    }
}
