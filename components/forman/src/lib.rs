use dlal_component_base::{component, json, serde_json, Arg, Body, CmdResult};

#[derive(Clone, Debug)]
struct Formant {
    freq: f32,
    amp: f32,
}

impl Formant {
    fn smooth(&mut self, other: &Formant, smoothness: f32) {
        self.freq = self.freq * smoothness + other.freq * (1.0 - smoothness);
        self.amp = self.amp * smoothness + other.amp * (1.0 - smoothness);
    }
}

impl Arg for Formant {
    fn from_value(value: &serde_json::Value) -> Option<Self> {
        let freq = value.get("freq")?.as_f64()? as f32;
        let amp = value.get("amp")?.as_f64()? as f32;
        Some(Self { freq, amp })
    }
}

component!(
    {"in": ["cmd"], "out": ["cmd"]},
    [
        "uni",
        {"name": "field_helpers", "fields": ["freq_per_bin"], "kinds": ["rw", "json"]},
    ],
    {
        formants: Vec<Formant>,
        formants_e: Vec<Formant>,
        formants_f: Vec<Formant>,
        spectrum: Vec<f32>,
        freq_per_bin: f32,
    },
    {
        "formants": {
            "args": [{"name": "formants"}],
        },
        "zero": {
            "args": [],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.spectrum = vec![0.0; 64];
    }

    fn run(&mut self) {
        if self.formants.is_empty() {
            return;
        }
        // smooth formants
        for i in 0..self.formants.len() {
            self.formants_e[i].smooth(&self.formants_f[i], 0.8);
            self.formants[i].smooth(&self.formants_e[i], 0.8);
        }
        // create spectrum
        for i in &mut self.spectrum {
            *i = 0.0;
        }
        let spread = 4;
        for formant in &mut self.formants {
            let a = ((formant.freq / self.freq_per_bin) as isize - spread).max(0) as usize;
            let b = ((formant.freq / self.freq_per_bin) as isize + spread).min(self.spectrum.len() as isize) as usize;
            for i in a..(b + 1) {
                let d = (formant.freq / self.freq_per_bin) - (i as f32);
                let d2 = d * d + 1.0;
                self.spectrum[i] += formant.amp / d2;
            }
        }
        // send to output
        let output = match &self.output {
            Some(v) => v,
            _ => return,
        };
        output.command(&json!({
            "name": "spectrum",
            "args": [self.spectrum],
        }));
    }
}

impl Component {
    fn formants_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.formants_f = body.arg(0)?;
        if self.formants.len() != self.formants_f.len() {
            self.formants = self.formants_f.clone();
            self.formants_e = self.formants_f.clone();
        }
        if self.formants.iter().all(|i| i.amp < 1e-2) {
            for i in 0..self.formants_f.len() {
                self.formants[i].freq = self.formants_f[i].freq;
                self.formants_e[i].freq = self.formants_f[i].freq;
            }
        }
        Ok(None)
    }

    fn zero_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        for i in &mut self.formants_f {
            i.amp = 0.0;
        }
        Ok(None)
    }
}
