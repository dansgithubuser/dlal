use dlal_component_base::{arg_num, command, err, gen_component, json, kwarg_num};

use multiqueue2::{MPMCSender, MPMCUniReceiver};

pub struct Specifics {
    audio: Vec<f32>,
    send: Option<MPMCSender<f32>>,
    recv: Option<MPMCUniReceiver<f32>>,
    size: u64,
}

gen_component!(Specifics);

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
        command!(
            commands,
            "join",
            |soul, body| {
                soul.audio.resize(kwarg_num(&body, "samples_per_evaluation")?, 0.0);
                Ok(None)
            },
            { "kwargs": ["samples_per_evaluation"] },
        );
        command!(
            commands,
            "resize",
            |soul, body| {
                soul.resize(arg_num(&body, 0)?);
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
                    return err!("not initialized");
                }
                let size: usize = arg_num(&body, 0)?;
                let mut audio = Vec::<String>::new();
                for _ in 0..size {
                    audio.push(soul.recv.as_ref().unwrap().recv().unwrap().to_string());
                }
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
                soul.resize(arg_num(&body, 0)?);
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
