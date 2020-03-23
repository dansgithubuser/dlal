use dlal_component_base::{err, gen_component, json, View};

use midir::{MidiInput, MidiInputConnection};
use multiqueue2::{MPMCSender, MPMCUniReceiver};

fn new_midi_in() -> MidiInput {
    MidiInput::new("midir test input").expect("MidiInput::new failed")
}

pub struct Specifics {
    conn: Option<MidiInputConnection<MPMCSender<u8>>>,
    recv: Option<MPMCUniReceiver<u8>>,
    msg: Vec<u8>,
    views: Vec<View>,
}

gen_component!(Specifics);

impl Specifics {
    fn get_ports(&self) -> Vec<String> {
        let midi_in = new_midi_in();
        (0..midi_in.port_count())
            .map(|i| midi_in.port_name(i).expect("port_name failed"))
            .collect()
    }

    fn open(&mut self, port: usize) {
        let midi_in = new_midi_in();
        let (send, recv) = multiqueue2::mpmc_queue(256);
        self.recv = Some(recv.into_single().expect("into_single failed"));
        self.conn = Some(
            midi_in
                .connect(
                    port,
                    "dlal-midir-input",
                    move |_timestamp_us, msg, send| {
                        for i in msg {
                            send.try_send(*i).expect("try_send failed");
                        }
                    },
                    send,
                )
                .expect("MidiIn::connect failed"),
        );
    }
}

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Specifics {
            conn: None,
            recv: None,
            msg: Vec::with_capacity(8),
            views: Vec::with_capacity(1),
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        commands.insert(
            "ports",
            Command {
                func: |soul, _body| {
                    Ok(Some(json!({
                        "result": soul.get_ports(),
                    })))
                },
                info: json!({}),
            },
        );
        commands.insert(
            "open",
            Command {
                func: |soul, body| {
                    let port = match body["args"][0].as_str() {
                        Some(port) => port,
                        None => return Err(err("port isn't a string")),
                    };
                    let ports = soul.get_ports();
                    for (i, v) in ports.iter().enumerate() {
                        if v.starts_with(port) {
                            soul.open(i);
                            return Ok(None);
                        }
                    }
                    Err(err("no such port"))
                },
                info: json!({
                    "args": ["port_name_prefix"],
                }),
            },
        );
        commands.insert(
            "connect",
            Command {
                func: |soul, body| {
                    soul.views.push(View::new(&body["args"])?);
                    Ok(None)
                },
                info: json!({
                    "args": ["component", "command", "audio", "midi", "evaluate"],
                }),
            },
        );
    }

    fn evaluate(&mut self) {
        if self.recv.is_none() {
            return;
        }
        loop {
            match self.recv.as_ref().unwrap().try_recv() {
                Ok(v) => {
                    if v & 0x80 != 0 && !self.msg.is_empty() {
                        for i in &self.views {
                            i.midi(&self.msg);
                        }
                        self.msg.clear();
                    }
                    self.msg.push(v);
                }
                Err(_) => return,
            }
        }
    }
}
