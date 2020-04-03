use dlal_component_base::{
    arg, arg_num, arg_str, command, err, gen_component, join, json, json_get, json_num, kwarg_num,
    multi, JsonValue, View,
};

use std::collections::HashMap;
use std::vec::Vec;

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

gen_component!(Specifics);

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
                    .resize(kwarg_num(&body, "samples_per_evaluation")?, 0.0);
                soul.sample_rate = kwarg_num(&body, "sample_rate")?;
                Ok(None)
            },
            ["samples_per_evaluation", "sample_rate"],
        );
        multi!(connect commands, true);
        command!(
            commands,
            "load",
            |soul, body| {
                let file_path = arg_str(&body, 0)?;
                let note: usize = arg_num(&body, 1)?;
                if note >= 128 {
                    return err!("invalid note");
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
            { "args": ["file_path", "note"] },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| {
                let mut sounds = HashMap::<String, JsonValue>::new();
                for (note, sound) in soul.sounds.iter().enumerate() {
                    if sound.samples.is_empty() {
                        continue;
                    }
                    sounds.insert(
                        note.to_string(),
                        json!({
                            "samples": sound.samples.iter().map(|i| i.to_string()).collect::<Vec<_>>(),
                            "sample_rate": sound.sample_rate.to_string(),
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
                let arg_sounds = arg(&body, 0)?
                    .as_object()
                    .ok_or_else(|| err!(box "sounds isn't an object"))?;
                for (note, arg_sound) in arg_sounds.iter() {
                    let note: usize = note.parse()?;
                    let mut sound = Sound::default();
                    sound.sample_rate = json_num(json_get(arg_sound, "sample_rate")?)?;
                    let arg_samples = json_get(arg_sound, "samples")?
                        .as_array()
                        .ok_or_else(|| err!(box "samples isn't an array"))?;
                    for sample in arg_samples {
                        sound.samples.push(json_num(sample)?);
                    }
                    soul.sounds[note] = sound;
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
                self.audio[i] += sound.samples[sound.play_index as usize] * sound.play_vol;
                sound.play_index += sound.sample_rate as f32 / self.sample_rate as f32;
                if sound.play_index as usize >= sound.samples.len() {
                    sound.play_vol = 0.0;
                    break;
                }
            }
        }
        multi!(audio self.audio, self.outputs, self.audio.len());
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
