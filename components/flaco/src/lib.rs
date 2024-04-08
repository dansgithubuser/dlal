use dlal_component_base::{component, err, serde_json, Body, CmdResult};

use std::collections::VecDeque;
use std::fs;
use std::sync::mpsc::{sync_channel, SyncSender};
use std::thread;
use std::time::{Duration, Instant};

//===== Block =====//
const BLOCK_SIZE: usize = 4096;

#[derive(Clone)]
struct Block {
    audio: [f32; BLOCK_SIZE],
}

impl Default for Block {
    fn default() -> Self {
        Self {
            audio: [0.0; BLOCK_SIZE],
        }
    }
}

//===== Flacker =====//
struct Write {
    path: String,
    duration: Option<Duration>,
}

impl Write {
    fn end() -> Self {
        Self {
            path: String::from(""),
            duration: None,
        }
    }

    fn is_end(&self) -> bool {
        self.path.is_empty()
    }
}

struct Flacker {
    block_tx: SyncSender<Block>,
    write_tx: SyncSender<Write>,
}

impl Flacker {
    fn new(sample_rate: u32, context_duration: Duration) -> Self {
        let (block_tx, block_rx) = sync_channel::<Block>(16);
        let (write_tx, write_rx) = sync_channel::<Write>(16);
        let context_len_max = (context_duration.as_secs_f32() * sample_rate as f32 / BLOCK_SIZE as f32) as usize + 1;
        thread::spawn(move || {
            let mut context = VecDeque::<Block>::with_capacity(context_len_max + 1);
            let mut file: Option<std::fs::File> = None;
            let mut end_at: Option<Instant> = None;
            loop {
                // audio
                let block = match block_rx.recv() {
                    Ok(block) => block,
                    Err(_) => return,
                };
                context.push_back(block);
                if context.len() > context_len_max {
                    context.pop_front();
                }
                // write start & end
                loop {
                    match write_rx.try_recv() {
                        Ok(write) => {
                            if !write.is_end() {
                                if file.is_some() {
                                    continue;
                                }
                                match fs::File::create(&write.path) {
                                    Ok(f) => file = Some(f),
                                    Err(_) => continue,
                                }
                                if let Some(duration) = write.duration {
                                    end_at = Some(Instant::now() + duration);
                                }
                            } else {
                                file = None;
                                end_at = None;
                            }
                        }
                        Err(_) => break,
                    }
                }
                // write
                if let Some(file) = file.as_mut() {
                    loop {
                        match context.pop_front() {
                            Some(block) => Self::write(&block, sample_rate, file),
                            None => break,
                        }
                    }
                }
                // end automatically
                if let Some(t) = end_at {
                    if t < Instant::now() {
                        file = None;
                        end_at = None;
                    }
                }
            }
        });
        Self {
            block_tx,
            write_tx,
        }
    }

    fn write(block: &Block, sample_rate: u32, file: &mut fs::File) {
        let block = {
            let mut i32s = [0; BLOCK_SIZE];
            for i in 0..BLOCK_SIZE {
                i32s[i] = (block.audio[i] * 32767.0) as i32;
            }
            i32s
        };
        let encoder = flacenc::config::Encoder::default();
        let encoder = {
            use flacenc::error::Verify;
            encoder.into_verified().unwrap()
        };
        let flac_stream = flacenc::encode_with_fixed_block_size(
            &encoder,
            flacenc::source::MemSource::from_samples(
                &block,
                1, // channels
                16, // bit depth
                sample_rate as usize,
            ),
            BLOCK_SIZE,
        ).unwrap();
        let mut flac_sink = flacenc::bitsink::ByteSink::new();
        {
            use flacenc::component::BitRepr;
            flac_stream.write(&mut flac_sink).unwrap();
        }
        {
            use std::io::Write;
            file.write(flac_sink.as_slice()).unwrap();
        }
    }
}

//===== component =====//
component!(
    {"in": ["audio"], "out": []},
    [
        "audio",
        {"name": "field_helpers", "fields": ["context_duration"], "kinds": ["rw", "json"]},
    ],
    {
        context_duration: f32,
        block: Block,
        block_i: usize,
        flacker: Option<Flacker>,
    },
    {
        "write_start": {
            "args": [
                "path",
                {"name": "duration", "optional": true},
            ],
        },
        "write_end": {
            "args": [],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.context_duration = 0.0;
    }

    fn join(&mut self, body: serde_json::Value) -> CmdResult {
        let sample_rate: u32 = body.kwarg("sample_rate")?;
        self.flacker = Some(Flacker::new(
            sample_rate,
            Duration::from_secs_f32(self.context_duration),
        ));
        Ok(None)
    }

    fn run(&mut self) {
        for i in &mut self.audio {
            self.block.audio[self.block_i] = *i;
            *i = 0.0;
            self.block_i += 1;
            if self.block_i >= BLOCK_SIZE {
                self.flacker.as_ref().unwrap().block_tx.try_send(self.block.clone()).ok();
                self.block_i = 0;
            }
        }
    }
}

impl Component {
    fn write_start_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let write = Write {
            path: body.arg(0)?,
            duration: body.arg(1).ok().map(|s| Duration::from_secs_f32(s)),
        };
        self.flacker.as_ref().ok_or(err!("Not joined."))?.write_tx.send(write)?;
        Ok(None)
    }

    fn write_end_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        self.flacker.as_ref().ok_or(err!("Not joined."))?.write_tx.send(Write::end())?;
        Ok(None)
    }
}
