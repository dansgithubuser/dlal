use dlal_component_base::{component, err, serde_json, Body, CmdResult, View};

use multiqueue2::{MPMCSender, MPMCUniReceiver};

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
    to_audio_send: MPMCSender<QueuedItem>,
    to_audio_recv: MPMCUniReceiver<QueuedItem>,
    fro_audio_send: MPMCSender<Box<Option<serde_json::Value>>>,
    fro_audio_recv: MPMCUniReceiver<Box<Option<serde_json::Value>>>,
}

impl Default for Queues {
    fn default() -> Self {
        let (to_audio_send, to_audio_recv) = multiqueue2::mpmc_queue(128);
        let (fro_audio_send, fro_audio_recv) = multiqueue2::mpmc_queue(128);
        Self {
            to_audio_send,
            to_audio_recv: to_audio_recv.into_single().unwrap(),
            fro_audio_send,
            fro_audio_recv: fro_audio_recv.into_single().unwrap(),
        }
    }
}

component!(
    {"in": ["cmd"], "out": ["cmd"]},
    ["samples_per_evaluation", "uni"],
    {
        queues: Queues,
        wait: usize,
    },
    {
        "queue": {"args": ["component", "command", "audio", "midi", "evaluate", "body", "timeout_ms", "detach"]},
        "wait": {"args": ["samples"]},
    },
);

impl ComponentTrait for Component {
    fn evaluate(&mut self) {
        if self.wait > self.samples_per_evaluation {
            self.wait -= self.samples_per_evaluation;
            return;
        }
        while let Ok(item) = self.queues.to_audio_recv.try_recv() {
            match item {
                QueuedItem::Wait(wait) => {
                    self.wait = wait;
                    break;
                }
                QueuedItem::Command { view, body, detach } => {
                    let result = view.command(&*body);
                    if !detach {
                        self.queues
                            .fro_audio_send
                            .try_send(Box::new(result))
                            .expect("try_send failed");
                    }
                }
            }
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
        if self
            .queues
            .to_audio_send
            .try_send(QueuedItem::Command {
                view: View::new(&body.at("args")?)?,
                body: Box::new(body.arg(5)?),
                detach,
            })
            .is_err()
        {
            return Err(err!("try_send failed").into());
        }
        if detach {
            return Ok(None);
        }
        std::thread::sleep(std::time::Duration::from_millis(body.arg(6)?));
        Ok(*self.queues.fro_audio_recv.try_recv()?)
    }

    fn wait_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if self
            .queues
            .to_audio_send
            .try_send(QueuedItem::Wait(body.arg(0)?))
            .is_err()
        {
            return Err(err!("try_send failed").into());
        }
        Ok(None)
    }
}
