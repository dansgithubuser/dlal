use dlal_component_base::{component, err, json_to_ptr, serde_json, Body, CmdResult};

use std::collections::{hash_map, HashMap};

type Category = Vec<Vec<f32>>;

fn category_avg(category: Category) -> Category {
    if category.is_empty() {
        return Category::new();
    }
    let mut sum = vec![0.0; category[0].len()];
    for registers in &category {
        for (i, register) in registers.iter().enumerate() {
            sum[i] += register;
        }
    }
    let avg = sum.iter().map(|i| i / category.len() as f32).collect();
    vec![avg]
}

fn category_exclude(category: &mut Category, duration: f32, sample_rate: u32, run_size: usize) {
    let runs = (duration * (sample_rate as f32) / (run_size as f32)) as u32;
    for _ in 0..runs {
        category.pop();
    }
}

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
                "smoothness",
                "categories"
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
        categories: HashMap<String, Category>,
        category_sampling: Option<Category>,
    },
    {
        "stft": {
            "args": [{
                "name": "stft",
                "kind": "norm",
            }],
        },
        "sample_start": {
            "args": [],
            "desc": "Start sampling a category of sound.",
        },
        "sample_exclude": {
            "args": [
                {
                    "name": "duration",
                    "default": 1,
                    "unit": "seconds",
                },
            ],
            "desc": "Exclude specified past duration from sample.",
        },
        "sample_end": {
            "args": [
                "name",
                {
                    "name": "exclude_duration",
                    "default": 1,
                    "unit": "seconds",
                },
            ],
            "desc": "End sample, and give it a name. Exclude specified past duration from sample.",
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
        }
        if let Some(category_sampling) = self.category_sampling.as_mut() {
            category_sampling.push(self.registers.clone());
        }
        Ok(None)
    }

    fn sample_start_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        if self.category_sampling.is_some() {
            return Err(err!("Already sampling.").into());
        }
        self.category_sampling = Some(Category::new());
        Ok(None)
    }

    fn sample_exclude_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let mut category_sampling = match self.category_sampling.as_mut() {
            Some(v) => v,
            None => return Err(err!("Not sampling.").into()),
        };
        let duration: f32 = body.arg(0).unwrap_or(1.0);
        category_exclude(&mut category_sampling, duration, self.sample_rate, self.run_size);
        Ok(None)
    }

    fn sample_end_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let mut category_sampling = match self.category_sampling.take() {
            Some(v) => v,
            None => return Err(err!("Not sampling.").into()),
        };
        let name: String = body.arg(0)?;
        let duration: f32 = body.arg(1).unwrap_or(1.0);
        category_exclude(&mut category_sampling, duration, self.sample_rate, self.run_size);
        match self.categories.entry(name) {
            hash_map::Entry::Vacant(i) => {
                i.insert(category_avg(category_sampling));
            }
            hash_map::Entry::Occupied(_) => {}
        }
        Ok(None)
    }
}
