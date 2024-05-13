use dlal_component_base::{component, err, json, serde_json, Body, CmdResult};

enum WavSamples {
    Float(hound::WavIntoSamples<std::io::BufReader<std::fs::File>, f32>),
    Int16(hound::WavIntoSamples<std::io::BufReader<std::fs::File>, i16>),
}

enum Reader {
    None,
    Flac(claxon::FlacReader<std::fs::File>),
    Wav(WavSamples, u32),
}

impl Default for Reader {
    fn default() -> Self {
        Reader::None
    }
}

component!(
    {"in": [""], "out": ["audio"]},
    [
        "run_size",
        "sample_rate",
        "uni",
        "check_audio",
        {
            "name": "field_helpers",
            "fields": ["playing"],
            "kinds": ["r"]
        },
    ],
    {
        reader: Reader,
        block: Vec<f32>,
        sample_i: usize,
        playing: bool,
    },
    {
        "open": {
            "args": ["file path"],
        },
        "duration": {
            "args": [],
            "return": "number of samples",
        },
    },
);

impl ComponentTrait for Component {
    fn run(&mut self) {
        let output = match &self.output {
            Some(v) => v,
            None => return,
        };
        let audio = output.audio(self.run_size).unwrap();
        match &mut self.reader {
            Reader::None => return,
            Reader::Flac(reader) => for i in 0..self.run_size {
                if self.sample_i == self.block.len() {
                    self.block = match reader.blocks().read_next_or_eof(vec![]) {
                        Ok(Some(block)) => {
                            (0..block.duration())
                                .map(|i| block.sample(0, i) as f32 / 0x8000 as f32)
                                .collect()
                        }
                        _ => {
                            self.playing = false;
                            return;
                        }
                    };
                    self.sample_i = 0;
                }
                audio[i] += self.block[self.sample_i];
                self.sample_i += 1;
            },
            Reader::Wav(samples, _) => for i in 0..self.run_size {
                audio[i] += match samples {
                    WavSamples::Float(samples) => match samples.next() {
                        Some(Ok(sample)) => sample,
                        _ => {
                            self.playing = false;
                            return;
                        }
                    },
                    WavSamples::Int16(samples) => match samples.next() {
                        Some(Ok(sample)) => sample as f32 / 32768.0,
                        _ => {
                            self.playing = false;
                            return;
                        }
                    },
                };
                self.sample_i += 1;
            }
        }
    }
}

impl Component {
    fn open_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let file_path: String = body.arg(0)?;
        if file_path.ends_with(".flac") {
            self.reader = match claxon::FlacReader::open(&file_path) {
                Ok(v) => Reader::Flac(v),
                Err(e) => return Err(err!("{:?}", e).into()),
            };
        } else if file_path.ends_with(".wav") {
            let reader = hound::WavReader::open(file_path)?;
            let duration = reader.duration();
            let spec = reader.spec();
            self.reader = match (spec.sample_format, spec.bits_per_sample) {
                (hound::SampleFormat::Float, 32) => Reader::Wav(WavSamples::Float(reader.into_samples()), duration),
                (hound::SampleFormat::Int, 16) => Reader::Wav(WavSamples::Int16(reader.into_samples()), duration),
                _ => return Err(err!("Unhandled wav spec {:?}{}.", spec.sample_format, spec.bits_per_sample).into()),
            }
        }
        self.playing = true;
        Ok(None)
    }

    fn duration_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        match &self.reader {
            Reader::None => return Err(err!("No file opened.").into()),
            Reader::Flac(reader) => match reader.streaminfo().samples {
                Some(samples) => Ok(Some(json!(samples))),
                None => Err(err!("No samples.").into()),
            },
            Reader::Wav(_, duration) => Ok(Some(json!(duration))),
        }
    }
}
