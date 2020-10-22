use dlal_component_base::{component, err, json, serde_json, Body, CmdResult};

use multiqueue2::{MPMCSender, MPMCUniReceiver};

component!(
    {"in": ["audio"], "out": ["audio*"]},
    [
        {"name": "join_info", "value": {"kwargs": ["run_size"]}},
    ],
    {
        audio: Vec<f32>,
        send: Option<MPMCSender<f32>>,
        recv: Option<MPMCUniReceiver<f32>>,
        size: u64,
    },
    {
        "resize": {"args": ["size"]},
        "size": {},
        "clear": {},
        "read": {"args": ["size"]},
    },
);

impl Component {
    fn resize(&mut self, size: u64) {
        let (send, recv) = multiqueue2::mpmc_queue(size);
        self.send = Some(send);
        self.recv = Some(recv.into_single().expect("into_single failed"));
        self.size = size;
    }
}

impl ComponentTrait for Component {
    fn join(&mut self, body: serde_json::Value) -> CmdResult {
        let run_size = body.kwarg("run_size")?;
        self.audio.resize(run_size, 0.0);
        if self.size == 0 {
            self.resize(run_size as u64);
        }
        Ok(None)
    }

    fn run(&mut self) {
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

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!(self.size.to_string())))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.resize(body.arg(0)?);
        Ok(None)
    }
}

impl Component {
    fn resize_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.resize(body.arg(0)?);
        Ok(None)
    }

    fn size_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!(self.size.to_string())))
    }

    fn clear_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        while self.recv.as_ref().unwrap().try_recv().is_ok() {}
        Ok(None)
    }

    fn read_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if self.recv.is_none() {
            return Err(err!("not initialized").into());
        }
        let mut audio = Vec::<String>::new();
        match body.arg(0) {
            Ok(size) => {
                for _ in 0..size {
                    audio.push(self.recv.as_ref().unwrap().recv().unwrap().to_string());
                }
            }
            Err(_) => {
                while let Ok(x) = self.recv.as_ref().unwrap().try_recv() {
                    audio.push(x.to_string());
                }
            }
        };
        Ok(Some(json!(audio)))
    }
}
