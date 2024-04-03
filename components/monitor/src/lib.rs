use dlal_component_base::{component, err, json, json_to_ptr, serde_json, Body, CmdResult};

use std::collections::{hash_map, HashMap, HashSet};

//===== Registers =====//
type Registers = Vec<f32>;

fn registers_distance(a: &Registers, b: &Registers) -> f32 {
    if a.len() != b.len() {
        panic!("Different register lengths: {} vs {}", a.len(), b.len());
    }
    let mut d = 0.0;
    for i in 0..a.len() {
        d += (a[i] - b[i]).abs()
    }
    d
}

fn registers_amp(registers: &Registers) -> f32 {
    registers.iter().sum()
}

//===== Category =====//
type Category = Vec<Registers>;

fn category_avg(category: &Category) -> Registers {
    if category.is_empty() {
        return Registers::new();
    }
    let mut sum = vec![0.0; category[0].len()];
    for registers in category {
        for (i, register) in registers.iter().enumerate() {
            sum[i] += register;
        }
    }
    sum.iter().map(|i| i / category.len() as f32).collect()
}

fn category_exclude(category: &mut Category, duration: f32, sample_rate: u32, run_size: usize) {
    let runs = (duration * (sample_rate as f32) / (run_size as f32)) as u32;
    for _ in 0..runs {
        category.pop();
    }
}

fn category_distance(category: &Category, registers: &Registers) -> f32 {
    let mut distance: f32 = f32::MAX;
    for i in category {
        distance = distance.min(registers_distance(i, registers));
    }
    distance
}

fn category_amp(category: &Category) -> f32 {
    let mut amp: f32 = f32::MIN;
    for registers in category {
        amp = amp.max(registers_amp(registers));
    }
    amp
}

//===== Component =====//
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
        {
            "name": "field_helpers",
            "fields": [
                "registers",
                "category_detected",
                "category_distances"
            ],
            "kinds": ["r"]
        },
    ],
    {
        registers: Registers,
        register_count: usize,
        register_distance_factor: f32,
        register_width_factor: f32,
        smoothness: f32,
        categories: HashMap<String, Category>,
        category_sampling: Option<Category>,
        category_detected: Option<String>,
        category_distances: HashMap<String, f32>,
        categories_recent: HashSet<String>,
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
        "merge": {
            "args": ["src", "dst"],
            "desc": "src category will be merged into dst category. src category will be removed.",
        },
        "take_recent_categories": {
            "args": [],
            "desc": "Return categories detected since this was last called.",
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
        // stft to registers
        let data = json_to_ptr!(body.arg::<serde_json::Value>(0)?, *const f32);
        let len = body.arg(1)?;
        let stft = unsafe { std::slice::from_raw_parts(data, len) };
        if self.register_count != self.registers.len() {
            self.registers.resize(self.register_count, -10.0);
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
        // sample
        if let Some(category_sampling) = self.category_sampling.as_mut() {
            category_sampling.push(self.registers.clone());
        }
        // detect
        self.detect_known_category();
        self.detect_unknown_category();
        if let Some(category) = &self.category_detected {
            self.categories_recent.insert(category.clone());
        }
        //
        Ok(None)
    }

    fn take_recent_categories_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        let j = json!(self.categories_recent);
        self.categories_recent.clear();
        Ok(Some(j))
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
        let registers = category_avg(&category_sampling);
        match self.categories.entry(name) {
            hash_map::Entry::Vacant(i) => {
                i.insert(vec![registers]);
            }
            hash_map::Entry::Occupied(mut i) => {
                i.get_mut().push(registers);
            }
        }
        Ok(None)
    }

    fn merge_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let src: String = body.arg(0)?;
        let dst: String = body.arg(1)?;
        {
            let src = self.categories.get(&src).ok_or_else(|| err!("no such src category \"{}\"", src))?.clone();
            let dst = self.categories.get_mut(&dst).ok_or_else(|| err!("no such dst category \"{}\"", dst))?;
            dst.extend_from_slice(&src);
        }
        self.categories.remove(&src);
        Ok(None)
    }

    fn detect_known_category(&mut self) {
        let mut distance_silence: Option<f32> = None;
        let mut distance_min: Option<f32> = None;
        let mut category_min: Option<&String> = None;
        for (name, category) in self.categories.iter() {
            let distance = category_distance(category, &self.registers);
            match self.category_distances.get_mut(name) {
                Some(d) => {
                    *d = distance;
                }
                None => {
                    self.category_distances.insert(name.clone(), distance);
                }
            }
            if name == "silence" {
                distance_silence = Some(distance);
                continue;
            }
            match distance_min {
                None => {
                    distance_min = Some(distance);
                    category_min = Some(&name);
                }
                Some(distance_min_curr) => {
                    if distance < distance_min_curr {
                        distance_min = Some(distance);
                        category_min = Some(&name);
                    }
                }
            }
        }
        let distance_min = match distance_min {
            Some(distance_min) => distance_min,
            None => {
                self.category_detected = None;
                return;
            }
        };
        let distance_silence = match distance_silence {
            Some(distance_silence) => distance_silence,
            None => {
                self.category_detected = category_min.cloned();
                return;
            }
        };
        if distance_min * 3.0 < distance_silence {
            self.category_detected = category_min.cloned();
        } else {
            self.category_detected = None;
        }
    }

    fn detect_unknown_category(&mut self) {
        // Assert we aren't near a known category.
        if self.category_detected.is_some() {
            return;
        }
        // Assert we're not near silence.
        let amp_silence = match self.categories.get("silence") {
            Some(silence) => category_amp(silence),
            None => return, // Can't decide there's sound without knowing silence.
        };
        if registers_amp(&self.registers) < amp_silence + 1.0 {
            return;
        }
        // There's an unknown sound. Make a category.
        let name = format!("unknown-{}", self.categories.len());
        self.categories.insert(
            name.clone(),
            vec![self.registers.clone()],
        );
        self.category_detected = Some(name);
        // TODO: issue a cmd saying a category was detected
    }
}
