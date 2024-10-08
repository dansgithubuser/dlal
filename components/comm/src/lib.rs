use dlal_component_base::{component, err, serde_json, Body, CmdResult, View};

use std::sync::mpsc::{Receiver, sync_channel, SyncSender};

#[derive(Debug)]
enum QueuedItem {
    Command {
        view: View,
        body: Box<serde_json::Value>,
        detach: bool,
    },
    Wait(usize),
}

struct Queues {
    to_audio_send: SyncSender<QueuedItem>,
    to_audio_recv: Receiver<QueuedItem>,
    fro_audio_send: SyncSender<Box<Option<serde_json::Value>>>,
    fro_audio_recv: Receiver<Box<Option<serde_json::Value>>>,
}

impl Queues {
    fn new(size: usize) -> Self {
        let (to_audio_send, to_audio_recv) = sync_channel(size);
        let (fro_audio_send, fro_audio_recv) = sync_channel(size);
        Self {
            to_audio_send,
            to_audio_recv,
            fro_audio_send,
            fro_audio_recv,
        }
    }
}

impl Default for Queues {
    fn default() -> Self {
        Self::new(128)
    }
}

component!(
    {"in": ["cmd"], "out": ["cmd"]},
    [
        "run_size",
        "uni",
        {"name": "field_helpers", "fields": ["last_error"], "kinds": ["r"]},
        {"name": "field_helpers", "fields": ["pause"], "kinds": ["rw"]},
    ],
    {
        queues: Queues,
        wait: usize,
        pause: bool,
        last_error: String,
    },
    {
        "queue": {"args": ["component", "command", "audio", "midi", "run", "body", "timeout_ms", "detach"]},
        "wait": {"args": ["samples"]},
        "pause": {"args": ["enable"]},
        "resize": {"args": ["size"]},
    },
);

impl ComponentTrait for Component {
    fn run(&mut self) {
        if self.pause {
            return;
        }
        'outer: loop {
            if self.wait > self.run_size {
                self.wait -= self.run_size;
                return;
            }
            while let Ok(item) = self.queues.to_audio_recv.try_recv() {
                match item {
                    QueuedItem::Wait(wait) => {
                        self.wait += wait;
                        continue 'outer;
                    }
                    QueuedItem::Command { view, body, detach } => {
                        let result = view.command(&*body);
                        if !detach {
                            self.queues
                                .fro_audio_send
                                .try_send(Box::new(result))
                                .expect("try_send failed");
                        } else if let Some(result) = result {
                            if let Some(error) = result.get("error") {
                                self.last_error = error.as_str().unwrap_or(&error.to_string()).into();
                            }
                        }
                    }
                }
            }
            break;
        }
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(None)
    }

    fn from_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(None)
    }
}

impl Component {
    fn queue_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let detach = body.arg(7)?;
        if let Err(e) = self
            .queues
            .to_audio_send
            .try_send(QueuedItem::Command {
                view: View::new(&body.at("args")?)?,
                body: Box::new(body.arg(5)?),
                detach,
            })
        {
            return Err(err!("try_send failed: {}", e).into());
        }
        if detach {
            return Ok(None);
        }
        let t = std::time::Duration::from_millis(body.arg(6)?);
        Ok(*self.queues.fro_audio_recv.recv_timeout(t)?)
    }

    fn wait_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Err(e) = self
            .queues
            .to_audio_send
            .try_send(QueuedItem::Wait(body.arg(0)?))
        {
            return Err(err!("try_send failed: {}", e).into());
        }
        Ok(None)
    }

    fn resize_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        self.queues = Queues::new(body.arg(0)?);
        Ok(None)
    }
}
