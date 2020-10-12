use dlal_component_base::{Body, command, err, gen_component, join, View, serde_json};

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

pub struct Specifics {
    to_audio_send: MPMCSender<QueuedItem>,
    to_audio_recv: MPMCUniReceiver<QueuedItem>,
    fro_audio_send: MPMCSender<Box<Option<serde_json::Value>>>,
    fro_audio_recv: MPMCUniReceiver<Box<Option<serde_json::Value>>>,
    wait: usize,
    samples_per_evaluation: usize,
}

gen_component!(Specifics, {"in": ["cmd"], "out": ["cmd"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        let (to_audio_send, to_audio_recv) = multiqueue2::mpmc_queue(128);
        let (fro_audio_send, fro_audio_recv) = multiqueue2::mpmc_queue(128);
        Self {
            to_audio_send,
            to_audio_recv: to_audio_recv.into_single().expect("into_single failed"),
            fro_audio_send,
            fro_audio_recv: fro_audio_recv.into_single().expect("into_single failed"),
            wait: 0,
            samples_per_evaluation: 0,
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                soul.samples_per_evaluation = body.kwarg("samples_per_evaluation")?;
                Ok(None)
            },
            ["samples_per_evaluation"],
        );
        command!(
            commands,
            "queue",
            |soul, body| {
                let detach = body.arg(7)?;
                if let Err(_) = soul.to_audio_send
                    .try_send(QueuedItem::Command {
                        view: View::new(&body.at("args")?)?,
                        body: Box::new(body.arg(5)?),
                        detach,
                    }) {
                        Err(err!("try_send failed"))?;
                    }
                if detach {
                    return Ok(None);
                }
                std::thread::sleep(std::time::Duration::from_millis(body.arg(6)?));
                Ok(*soul.fro_audio_recv.try_recv()?)
            },
            { "args": ["component", "command", "audio", "midi", "evaluate", "body", "timeout_ms", "detach"] },
        );
        command!(
            commands,
            "wait",
            |soul, body| {
                if let Err(_) = soul.to_audio_send
                    .try_send(QueuedItem::Wait(
                        body.arg(0)?,
                    )) {
                        Err(err!("try_send failed"))?;
                    }
                Ok(None)
            },
            { "args": ["samples"] },
        );
    }

    fn evaluate(&mut self) {
        if self.wait > self.samples_per_evaluation {
            self.wait -= self.samples_per_evaluation;
            return;
        }
        while let Ok(item) = self.to_audio_recv.try_recv() {
            match item {
                QueuedItem::Wait(wait) => {
                    self.wait = wait;
                    break;
                }
                QueuedItem::Command { view, body, detach } => {
                    let result = view.command(&*body);
                    if !detach {
                        self.fro_audio_send
                            .try_send(Box::new(result))
                            .expect("try_send failed");
                    }
                }
            }
        }
    }
}
