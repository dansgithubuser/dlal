use dlal_component_base::{
    Arg, Body, command, gen_component, join, json, multi, serde_json, View, Error,
};

use std::cmp::min;
use std::collections::HashMap;

#[derive(Clone, Default)]
struct Sound {
    samples: Vec<f32>,
    sample_rate: u32,
    play_index: f32,
    play_vol: f32,
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
}

pub struct Specifics {
    audio: Vec<f32>,
    sample_rate: u32,
    outputs: Vec<View>,
    sounds: Vec<Sound>,
}

gen_component!(Specifics, {"in": ["audio*", "midi"], "out": ["audio"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            audio: Vec::new(),
            sample_rate: 0,
            outputs: Vec::with_capacity(1),
            sounds: vec![Sound::default(); 128],
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                soul.audio
                    .resize(body.kwarg("samples_per_evaluation")?, 0.0);
                soul.sample_rate = body.kwarg("sample_rate")?;
                Ok(None)
            },
            ["samples_per_evaluation", "sample_rate"],
        );
        multi!(connect commands, true);
        command!(
            commands,
            "set",
            |soul, body| {
                let samples = body.arg::<Vec<_>>(0)?.vec()?;
                for i in 0..min(samples.len(), soul.audio.len()) {
                    soul.audio[i] = samples[i];
                }
                Ok(None)
            },
            { "args": ["samples"] },
        );
        command!(
            commands,
            "load",
            |soul, body| {
                let file_path: String = body.arg(0)?;
                let note: usize = body.arg(1)?;
                if note >= 128 {
                    Error::err("invalid note")?;
                }
                let mut reader = hound::WavReader::open(file_path)?;
                let spec = reader.spec();
                let max = 1 << (spec.bits_per_sample - 1);
                let samples: Vec<f32> = match spec.sample_format {
                    hound::SampleFormat::Float => {
                        reader.samples::<f32>().map(
                            |i| i.unwrap()
                        ).collect()
                    },
                    hound::SampleFormat::Int => {
                        reader.samples::<i32>().map(
                            |i| i.unwrap() as f32 / max as f32
                        ).collect()
                    },
                };
                soul.sounds[note] = Sound {
                    samples,
                    sample_rate: spec.sample_rate,
                    ..Default::default()
                };
                Ok(None)
            },
            { "args": ["wav_file_path", "note"] },
        );
        command!(
            commands,
            "resample",
            |soul, body| {
                let ratio: f32 = body.arg(0)?;
                let note: usize = body.arg(1)?;
                if note >= 128 {
                    Error::err("invalid note")?;
                }
                let samples = &mut soul.sounds[note].samples;
                let mut resamples = Vec::<f32>::new();
                let mut index = 0.0;
                while (index as usize) < samples.len() {
                    resamples.push(samples[index as usize]);
                    index += ratio;
                }
                *samples = resamples;
                Ok(None)
            },
            { "args": ["ratio", "note"] },
        );
        command!(
            commands,
            "crop",
            |soul, body| {
                let start = (body.arg::<f32>(0)? * soul.sample_rate as f32) as usize;
                let end   = (body.arg::<f32>(1)? * soul.sample_rate as f32) as usize;
                if end < start {
                    Error::err("end is before start")?;
                }
                let note: usize = body.arg(2)?;
                if note >= 128 {
                    Error::err("invalid note")?;
                }
                let samples = &mut soul.sounds[note].samples;
                if start >= samples.len() {
                    Error::err("start is too late")?;
                }
                if end >= samples.len() {
                    Error::err("end is too late")?;
                }
                *samples = samples[start..end].to_vec();
                Ok(None)
            },
            { "args": ["start", "end", "note"] },
        );
        command!(
            commands,
            "clip",
            |soul, body| {
                let amplitude = body.arg(0)?;
                let note: usize = body.arg(1)?;
                if note >= 128 {
                    Error::err("invalid note")?;
                }
                for i in &mut soul.sounds[note].samples {
                    if *i > amplitude {
                        *i = amplitude;
                    } else if *i < -amplitude {
                        *i = -amplitude;
                    }
                }
                Ok(None)
            },
            { "args": ["amplitude", "note"] },
        );
        command!(
            commands,
            "amplify",
            |soul, body| {
                let amount: f32 = body.arg(0)?;
                let note: usize = body.arg(1)?;
                if note >= 128 {
                    Error::err("invalid note")?;
                }
                for sample in &mut soul.sounds[note].samples {
                    *sample *= amount;
                }
                Ok(None)
            },
            { "args": ["amount", "note"] },
        );
        command!(
            commands,
            "add",
            |soul, body| {
                let note_to: usize = body.arg(0)?;
                if note_to >= 128 {
                    Error::err("invalid note_to")?;
                }
                let note_from: usize = body.arg(1)?;
                if note_from >= 128 {
                    Error::err("invalid note_from")?;
                }
                if soul.sounds[note_from].samples.len() > soul.sounds[note_to].samples.len() {
                    let len = soul.sounds[note_from].samples.len();
                    soul.sounds[note_to].samples.resize(len, 0.0);
                }
                for i in 0..soul.sounds[note_from].samples.len() {
                    soul.sounds[note_to].samples[i] += soul.sounds[note_from].samples[i];
                }
                Ok(None)
            },
            { "args": ["note_to", "note_from"] },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| {
                let mut sounds = HashMap::<String, serde_json::Value>::new();
                for (note, sound) in soul.sounds.iter().enumerate() {
                    if sound.samples.is_empty() {
                        continue;
                    }
                    sounds.insert(
                        note.to_string(),
                        json!({
                            "samples": sound.samples,
                            "sample_rate": sound.sample_rate,
                        }),
                    );
                }
                Ok(Some(json!(sounds)))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                soul.sounds = vec![Sound::default(); 128];
                let sounds: serde_json::Map<String, serde_json::Value> = body.arg(0)?;
                for (note, sound) in sounds.iter() {
                    soul.sounds[note.parse::<usize>()?] = Sound {
                        sample_rate: sound.at("sample_rate")?,
                        samples: sound.at::<Vec<_>>("samples")?.vec()?,
                        ..Sound::default()
                    };
                }
                Ok(None)
            },
            {},
        );
    }

    fn evaluate(&mut self) {
        for sound in &mut self.sounds {
            if sound.play_vol == 0.0 {
                continue;
            }
            for i in 0..self.audio.len() {
                if sound.play_index as usize >= sound.samples.len() {
                    sound.play_vol = 0.0;
                } else {
                    self.audio[i] += sound.samples[sound.play_index as usize] * sound.play_vol;
                    sound.play_index += sound.sample_rate as f32 / self.sample_rate as f32;
                }
            }
        }
        multi!(audio self.audio, self.outputs, self.audio.len());
        for i in &mut self.audio {
            *i = 0.0;
        }
    }

    fn midi(&mut self, msg: &[u8]) {
        if msg.len() < 3 {
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
}
