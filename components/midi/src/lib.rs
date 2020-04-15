use dlal_component_base::{arg_str, command, err, gen_component, json, multi, View};

use midir::{MidiInput, MidiInputConnection};
use multiqueue2::{MPMCSender, MPMCUniReceiver};

const MSG_CAP: usize = 3;

fn new_midi_in() -> MidiInput {
    MidiInput::new("midir test input").expect("MidiInput::new failed")
}

pub struct Specifics {
    conn: Option<MidiInputConnection<MPMCSender<[u8; MSG_CAP]>>>,
    recv: Option<MPMCUniReceiver<[u8; MSG_CAP]>>,
    outputs: Vec<View>,
}

gen_component!(Specifics, {"in": ["midi**"], "out": ["midi"]});

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
        let conn = midi_in
            .connect(
                port,
                "dlal-midir-input",
                move |_timestamp_us, msg, send| {
                    if msg[0] >= 0xf0 {
                        return;
                    }
                    send.try_send([msg[0], msg[1], *msg.get(2).unwrap_or(&(0 as u8))])
                        .expect("try_send failed");
                },
                send,
            )
            .expect("MidiIn::connect failed");
        std::thread::sleep(std::time::Duration::from_millis(10));
        while self.recv.as_ref().unwrap().try_recv().is_ok() {}
        self.conn = Some(conn);
    }
}

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Specifics {
            conn: None,
            recv: None,
            outputs: Vec::with_capacity(1),
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        command!(
            commands,
            "ports",
            |soul, _body| Ok(Some(json!(soul.get_ports()))),
            {},
        );
        command!(
            commands,
            "open",
            |soul, body| {
                let port = arg_str(&body, 0)?;
                let ports = soul.get_ports();
                for (i, v) in ports.iter().enumerate() {
                    if v.starts_with(port) {
                        soul.open(i);
                        return Ok(None);
                    }
                }
                err!("no such port")
            },
            { "args": ["port_name_prefix"] },
        );
        multi!(connect commands, false);
    }

    fn evaluate(&mut self) {
        if self.recv.is_none() {
            return;
        }
        loop {
            match self.recv.as_ref().unwrap().try_recv() {
                Ok(msg) => {
                    multi!(midi msg, self.outputs);
                }
                Err(_) => return,
            }
        }
    }
}
