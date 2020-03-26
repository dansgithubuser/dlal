use dlal_component_base::{arg, arg_num, args, gen_component, json, JsonValue, View};

use multiqueue2::{MPMCSender, MPMCUniReceiver};

#[derive(Debug)]
struct QueuedCommand {
    view: View,
    body: Box<JsonValue>,
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
        let (to_audio_send, to_audio_recv) = multiqueue2::mpmc_queue(4);
        let (fro_audio_send, fro_audio_recv) = multiqueue2::mpmc_queue(4);
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
                    soul.to_audio_send
                        .try_send(QueuedCommand {
                            view: View::new(args(&body)?)?,
                            body: Box::new(arg(&body, 5)?.clone()),
                        })
                        .expect("try_send failed");
                    match arg_num(&body, 6) {
                        Ok(timeout_ms) => std::thread::sleep(std::time::Duration::from_millis(timeout_ms)),
                        Err(_) => return Ok(None),
                    };
                    Ok(*soul.fro_audio_recv.try_recv()?)
                }),
                info: json!({
                    "args": ["component", "command", "audio", "midi", "evaluate", "body", "timeout_ms"],
                }),
            },
        );
    }

    fn evaluate(&mut self) {
        loop {
            match self.to_audio_recv.try_recv() {
                Ok(queued_command) => self
                    .fro_audio_send
                    .try_send(Box::new(queued_command.view.command(*queued_command.body)))
                    .expect("try_send failed"),
                Err(_) => break,
            };
        }
    }
}
