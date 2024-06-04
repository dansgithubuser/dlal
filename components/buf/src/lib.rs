use dlal_component_base::{component, err, json, serde_json, Body, CmdResult};

use std::cmp::min;
use std::collections::HashMap;
use std::path::Path;

//===== Sound =====//
#[derive(Clone)]
struct Sound {
    samples: Vec<f32>,
    sample_rate: u32,
    cresc: f32,
    accel: f32,
    repeat: bool,
    play_index: f32,
    play_vol: f32,
    play_speed: f32,
}

impl Default for Sound {
    fn default() -> Self {
        Self {
            samples: Vec::new(),
            sample_rate: 0,
            cresc: 1.0,
            accel: 1.0,
            repeat: false,
            play_index: 0.0,
            play_vol: 0.0,
            play_speed: 1.0,
        }
    }
}

impl Sound {
    fn start(&mut self, vol: f32) {
        if self.samples.is_empty() {
            return;
        }
        self.play_index = 0.0;
        self.play_vol = vol;
    }

    fn stop(&mut self) {
        self.play_vol = 0.0;
    }

    fn playing(&self) -> bool {
        self.play_vol != 0.0
    }

    fn run_update(&mut self, sample_rate: u32, run_size: usize) {
        self.play_vol *= self.cresc.powf(run_size as f32 / sample_rate as f32);
        self.play_speed *= self.accel.powf(run_size as f32 / sample_rate as f32);
    }

    fn next(&mut self, sample_rate: u32) -> f32 {
        if self.play_index as usize >= self.samples.len() {
            if self.repeat {
                self.play_index = 0.0;
            } else {
                self.play_vol = 0.0;
                return 0.0;
            }
        }
        let ret = self.samples[self.play_index as usize] * self.play_vol;
        self.play_index += self.sample_rate as f32 / sample_rate as f32 * self.play_speed;
        ret
    }
}

//===== component =====//
component!(
    {"in": ["audio*", "midi"], "out": ["audio"]},
    [
        "sample_rate",
        "run_size",
        "multi",
        {"name": "field_helpers", "fields": ["repeat", "repeat_start", "repeat_end"], "kinds": []},
    ],
    {
        audio: Vec<f32>,
        sounds: Vec<Sound>,
        repeat: bool,
        repeat_start: f32,
        repeat_end: f32,
    },
    {
        "set": {"args": ["samples"]},
        "load": {"args": ["file_path", "note"]},
        "sound_params": {"args": ["note"], "kwargs": ["cresc", "accel", "repeat"]},
        "resample": {"args": ["ratio", "note"]},
        "crop": {"args": ["start", "end", "note"]},
        "clip": {"args": ["amplitude", "note"]},
        "amplify": {"args": ["amount", "note"]},
        "add": {"args": ["note_augend", "note_addend"]},
        "mul": {"args": ["note_multiplicand", "note_multiplier"]},
        "sin": {"args": ["amplitude", "frequency", "offset", "duration", "note"]},
        "repeat": {
            "args": ["enable"],
            "kwargs": [
                {
                    "name": "start",
                    "desc": "seconds into sound to repeat to",
                },
                {
                    "name": "end",
                    "desc": "seconds before end of sound to repeat from",
                },
            ],
        },
        "normalize": {"args": ["amplitude"]},
    },
);

impl ComponentTrait for Component {
    fn join(&mut self, _body: serde_json::Value) -> CmdResult {
        self.audio.resize(self.run_size, 0.0);
        Ok(None)
    }

    fn run(&mut self) {
        for sound in &mut self.sounds {
            if !sound.playing() {
                continue;
            }
            if self.repeat && sound.play_index > sound.samples.len() as f32 - self.repeat_end {
                sound.play_index = self.repeat_start;
            }
            sound.run_update(self.sample_rate, self.run_size);
            for i in 0..self.audio.len() {
                self.audio[i] += sound.next(self.sample_rate);
            }
        }
        self.multi_audio(&self.audio);
        for i in &mut self.audio {
            *i = 0.0;
        }
    }

    fn midi(&mut self, msg: &[u8]) {
        if msg.len() < 3 {
            return;
        }
        if self.sounds.is_empty() {
            return;
        }
        match msg[0] & 0xf0 {
            0x80 => {
                self.sounds[msg[1] as usize].stop();
            }
            0x90 => {
                if msg[2] == 0 {
                    self.sounds[msg[1] as usize].stop();
                } else {
                    self.sounds[msg[1] as usize].start(msg[2] as f32 / 127.0);
                }
            }
            _ => (),
        };
    }

    fn audio(&mut self) -> Option<&mut [f32]> {
        Some(self.audio.as_mut_slice())
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        let mut sounds = HashMap::<String, serde_json::Value>::new();
        for (note, sound) in self.sounds.iter().enumerate() {
            if sound.samples.is_empty() {
                continue;
            }
            sounds.insert(
                note.to_string(),
                json!({
                    "samples": sound.samples,
                    "sample_rate": sound.sample_rate,
                    "cresc": sound.cresc,
                    "accel": sound.accel,
                    "repeat": sound.repeat,
                }),
            );
        }
            
        Ok(Some(field_helper_to_json!(self, {
            "sounds": sounds,
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = field_helper_from_json!(self, body);
        let sounds: serde_json::Map<String, serde_json::Value> = j.at("sounds")?;
        if !sounds.is_empty() {
            self.ensure_sounds();
            for (note, sound) in sounds.iter() {
                self.sounds[note.parse::<usize>()?] = Sound {
                    sample_rate: sound.at("sample_rate")?,
                    samples: sound.at("samples")?,
                    cresc: sound.at("cresc")?,
                    accel: sound.at("accel")?,
                    repeat: sound.at("repeat")?,
                    ..Sound::default()
                };
            }
        }
        Ok(None)
    }
}

//----- helpers -----//
impl Component {
    fn ensure_sounds(&mut self) {
        if self.sounds.is_empty() {
            self.sounds.resize(128, Default::default());
        }
    }
}

//----- cmds -----//
impl Component {
    fn set_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let samples = body.arg::<Vec<_>>(0)?;
        for i in 0..min(samples.len(), self.audio.len()) {
            self.audio[i] = samples[i];
        }
        Ok(None)
    }

    fn load_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.ensure_sounds();
        let file_path: String = body.arg(0)?;
        let note: usize = body.arg(1)?;
        if !Path::new(&file_path).exists() {
            return Err(err!("no such file {}", file_path).into());
        }
        if note >= 128 {
            return Err(err!("invalid note").into());
        }
        let mut sound = Sound { ..Default::default() };
        if file_path.ends_with(".wav") {
            let mut reader = hound::WavReader::open(file_path)?;
            let spec = reader.spec();
            let max = 1 << (spec.bits_per_sample - 1);
            sound.samples = match spec.sample_format {
                hound::SampleFormat::Float => reader.samples::<f32>().map(|i| i.unwrap()).collect(),
                hound::SampleFormat::Int => reader
                    .samples::<i32>()
                    .map(|i| i.unwrap() as f32 / max as f32)
                    .collect(),
            };
            sound.sample_rate = spec.sample_rate;
        } else if file_path.ends_with(".flac") {
            let mut stream = match flac::StreamReader::<std::fs::File>::from_file(&file_path) {
                Ok(v) => v,
                Err(e) => return Err(err!("{:?}", e).into()),
            };
            let info = stream.info();
            for (i, v) in stream.iter::<i16>().enumerate() {
                if i % info.channels as usize != 0 {
                    continue;
                }
                sound.samples.push(v as f32 / 0x7fff as f32);
            }
            sound.sample_rate = info.sample_rate;
        } else {
            return Err(err!("unknown file extension").into());
        }
        self.sounds[note] = sound;
        Ok(None)
    }

    fn sound_params_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let note: usize = body.arg(0)?;
        let sound = &mut self.sounds.get_mut(note).ok_or("invalid note")?;
        if let Ok(cresc) = body.kwarg("cresc") {
            sound.cresc = cresc;
        }
        if let Ok(accel) = body.kwarg("accel") {
            sound.accel = accel;
        }
        if let Ok(repeat) = body.kwarg("repeat") {
            sound.repeat = repeat;
        }
        Ok(Some(json!({
            "cresc": sound.cresc,
            "accel": sound.accel,
            "repeat": sound.repeat,
        })))
    }

    fn resample_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let ratio: f32 = body.arg(0)?;
        let note: usize = body.arg(1)?;
        let samples = &mut self.sounds.get_mut(note).ok_or("invalid note")?.samples;
        let mut resamples = Vec::<f32>::new();
        let mut index = 0.0;
        while (index as usize) < samples.len() {
            resamples.push(samples[index as usize]);
            index += ratio;
        }
        *samples = resamples;
        Ok(None)
    }

    fn crop_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let start = (body.arg::<f32>(0)? * self.sample_rate as f32) as usize;
        let end = (body.arg::<f32>(1)? * self.sample_rate as f32) as usize;
        if end < start {
            return Err(err!("end is before start").into());
        }
        let note: usize = body.arg(2)?;
        let samples = &mut self.sounds.get_mut(note).ok_or("invalid note")?.samples;
        if start >= samples.len() {
            return Err(err!("start is too late").into());
        }
        if end >= samples.len() {
            return Err(err!("end is too late").into());
        }
        *samples = samples[start..end].to_vec();
        Ok(None)
    }

    fn clip_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let amplitude = body.arg(0)?;
        let note: usize = body.arg(1)?;
        for i in &mut self.sounds.get_mut(note).ok_or("invalid note")?.samples {
            if *i > amplitude {
                *i = amplitude;
            } else if *i < -amplitude {
                *i = -amplitude;
            }
        }
        Ok(None)
    }

    fn amplify_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let amount: f32 = body.arg(0)?;
        let note: usize = body.arg(1)?;
        for sample in &mut self.sounds.get_mut(note).ok_or("invalid note")?.samples {
            *sample *= amount;
        }
        Ok(None)
    }

    fn add_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let note_augend: usize = body.arg(0)?;
        if note_augend >= self.sounds.len() {
            return Err(err!("invalid note_augend").into());
        }
        let note_addend: usize = body.arg(1)?;
        if note_addend >= self.sounds.len() {
            return Err(err!("invalid note_addend").into());
        }
        if self.sounds[note_addend].samples.len() > self.sounds[note_augend].samples.len() {
            let len = self.sounds[note_addend].samples.len();
            self.sounds[note_augend].samples.resize(len, 0.0);
        }
        for i in 0..self.sounds[note_addend].samples.len() {
            self.sounds[note_augend].samples[i] += self.sounds[note_addend].samples[i];
        }
        Ok(None)
    }

    fn mul_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let note_multiplicand: usize = body.arg(0)?;
        if note_multiplicand >= self.sounds.len() {
            return Err(err!("invalid note_multiplicand").into());
        }
        let note_multiplier: usize = body.arg(1)?;
        if note_multiplier >= self.sounds.len() {
            return Err(err!("invalid note_multiplicand").into());
        }
        if self.sounds[note_multiplier].samples.len() < self.sounds[note_multiplicand].samples.len() {
            let len = self.sounds[note_multiplier].samples.len();
            self.sounds[note_multiplicand].samples.resize(len, 0.0);
        }
        for i in 0..self.sounds[note_multiplicand].samples.len() {
            self.sounds[note_multiplicand].samples[i] *= self.sounds[note_multiplier].samples[i];
        }
        Ok(None)
    }

    fn sin_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let amp: f32 = body.arg(0)?;
        let freq: f32 = body.arg(1)?;
        let offset: f32 = body.arg(2)?;
        let duration: f32 = body.arg(3)?;
        let note: usize = body.arg(4)?;
        self.ensure_sounds();
        if note >= self.sounds.len() {
            return Err(err!("invalid note").into());
        }
        let len = (duration * self.sample_rate as f32) as usize;
        let mut sin = vec![0.0; len];
        for i in 0..len {
            let phase =  i as f32 / self.sample_rate as f32 * freq * std::f32::consts::TAU;
            sin[i] = amp * phase.sin() + offset;
        }
        self.sounds[note] = Sound::default();
        self.sounds[note].samples = sin;
        self.sounds[note].sample_rate = self.sample_rate;
        Ok(None)
    }

    fn repeat_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.repeat = body.arg(0).unwrap_or(true);
        if self.repeat {
            self.repeat_start = body.kwarg("start").unwrap_or(0.2) * self.sample_rate as f32;
            self.repeat_end = body.kwarg("end").unwrap_or(0.2) * self.sample_rate as f32;
        }
        Ok(None)
    }

    fn normalize_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let amount: f32 = body.arg(0)?;
        for sound in &mut self.sounds {
            let m = amount / sound.samples.iter().fold(0.0, |a, i| f32::max(a, *i));
            for sample in &mut sound.samples {
                *sample *= m;
            }
        }
        Ok(None)
    }
}
