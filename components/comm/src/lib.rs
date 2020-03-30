use dlal_component_base::{arg, arg_num, args, err, gen_component, json, JsonValue, View};

use multiqueue2::{MPMCSender, MPMCUniReceiver};

#[derive(Debug)]
struct QueuedCommand {
    view: View,
    body: Box<JsonValue>,
    detach: bool,
}

pub struct Specifics {
    to_audio_send: MPMCSender<QueuedCommand>,
    to_audio_recv: MPMCUniReceiver<QueuedCommand>,
    fro_audio_send: MPMCSender<Box<Option<JsonValue>>>,
    fro_audio_recv: MPMCUniReceiver<Box<Option<JsonValue>>>,
}

gen_component!(Specifics);

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        let (to_audio_send, to_audio_recv) = multiqueue2::mpmc_queue(64);
        let (fro_audio_send, fro_audio_recv) = multiqueue2::mpmc_queue(64);
        Self {
            to_audio_send,
            to_audio_recv: to_audio_recv.into_single().expect("into_single failed"),
            fro_audio_send,
            fro_audio_recv: fro_audio_recv.into_single().expect("into_single failed"),
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        commands.insert(
            "queue",
            Command {
                func: Box::new(|soul, body| {
                    let detach = match arg(&body, 7)?.as_bool() {
                        Some(v) => v,
                        None => return Err(err("detach isn't Boolean")),
                    };
                    soul.to_audio_send
                        .try_send(QueuedCommand {
                            view: View::new(args(&body)?)?,
                            body: Box::new(arg(&body, 5)?.clone()),
                            detach,
                        })
                        .expect("try_send failed");
                    if detach {
                        return Ok(None);
                    }
                    std::thread::sleep(std::time::Duration::from_millis(arg_num(&body, 6)?));
                    Ok(*soul.fro_audio_recv.try_recv()?)
                }),
                info: json!({
                    "args": ["component", "command", "audio", "midi", "evaluate", "body", "timeout_ms", "detach"],
                }),
            },
        );
    }

    fn evaluate(&mut self) {
        while let Ok(queued_command) = self.to_audio_recv.try_recv() {
            let result = queued_command.view.command(*queued_command.body);
            if !queued_command.detach {
                self.fro_audio_send
                    .try_send(Box::new(result))
                    .expect("try_send failed");
            }
        }
    }
}
