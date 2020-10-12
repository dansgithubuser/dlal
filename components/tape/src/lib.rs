use dlal_component_base::{command, gen_component, join, json, Body, err};

use multiqueue2::{MPMCSender, MPMCUniReceiver};

pub struct Specifics {
    audio: Vec<f32>,
    send: Option<MPMCSender<f32>>,
    recv: Option<MPMCUniReceiver<f32>>,
    size: u64,
}

gen_component!(Specifics, {"in": ["audio"], "out": ["audio*"]});

impl Specifics {
    fn resize(&mut self, size: u64) {
        let (send, recv) = multiqueue2::mpmc_queue(size);
        self.send = Some(send);
        self.recv = Some(recv.into_single().expect("into_single failed"));
        self.size = size;
    }
}

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            audio: Vec::new(),
            send: None,
            recv: None,
            size: 0,
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                let samples_per_evaluation = body.kwarg("samples_per_evaluation")?;
                soul.audio.resize(samples_per_evaluation, 0.0);
                if soul.size == 0 {
                    soul.resize(samples_per_evaluation as u64);
                }
                Ok(None)
            },
            ["samples_per_evaluation"],
        );
        command!(
            commands,
            "resize",
            |soul, body| {
                soul.resize(body.arg(0)?);
                Ok(None)
            },
            {
                "args": ["size"],
            },
        );
        command!(
            commands,
            "size",
            |soul, _body| { Ok(Some(json!(soul.size.to_string()))) },
            {},
        );
        command!(
            commands,
            "clear",
            |soul, _body| {
                while let Ok(_) = soul.recv.as_ref().unwrap().try_recv() {}
                Ok(None)
            },
            {},
        );
        command!(
            commands,
            "read",
            |soul, body| {
                if soul.recv.is_none() {
                    Err(err!("not initialized"))?;
                }
                let mut audio = Vec::<String>::new();
                match body.arg(0) {
                    Ok(size) =>  {
                        for _ in 0..size {
                            audio.push(soul.recv.as_ref().unwrap().recv().unwrap().to_string());
                        }
                    }
                    Err(_) => {
                        loop {
                            if let Ok(x) = soul.recv.as_ref().unwrap().try_recv() {
                                audio.push(x.to_string());
                            } else {
                                break;
                            }
                        }
                    }
                };
                Ok(Some(json!(audio)))
            },
            {
                "args": ["size"],
            },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| { Ok(Some(json!(soul.size.to_string()))) },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                soul.resize(body.arg(0)?);
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn evaluate(&mut self) {
        if self.send.is_none() {
            return;
        }
        for i in &mut self.audio {
            self.send.as_ref().unwrap().try_send(*i).ok();
            *i = 0.0;
        }
    }

    fn audio(&mut self) -> Option<&mut [f32]> {
        Some(self.audio.as_mut_slice())
    }
}
