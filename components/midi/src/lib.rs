use dlal_component_base::{component, err, json, serde_json, Body, CmdResult};

use midir::{MidiInput, MidiInputConnection};
use multiqueue2::{MPMCSender, MPMCUniReceiver};

const MSG_CAP: usize = 3;

fn new_midi_in() -> MidiInput {
    MidiInput::new("midir test input").expect("MidiInput::new failed")
}

component!(
    {"in": ["midi**"], "out": ["midi"]},
    ["multi"],
    {
        conn: Option<MidiInputConnection<MPMCSender<[u8; MSG_CAP]>>>,
        recv: Option<MPMCUniReceiver<[u8; MSG_CAP]>>,
    },
    {
        "ports": {},
        "open": {"args": ["port_name_prefix"]},
    },
);

impl Component {
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

impl ComponentTrait for Component {
    fn midi(&mut self, msg: &[u8]) {
        self.multi_midi(msg);
    }

    fn evaluate(&mut self) {
        if self.recv.is_none() {
            return;
        }
        loop {
            match self.recv.as_ref().unwrap().try_recv() {
                Ok(msg) => {
                    self.multi_midi(&msg);
                }
                Err(_) => return,
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
    fn ports_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!(self.get_ports())))
    }

    fn open_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let port: String = body.arg(0)?;
        let ports = self.get_ports();
        for (i, v) in ports.iter().enumerate() {
            if v.starts_with(&port) {
                self.open(i);
                return Ok(None);
            }
        }
        Err(err!("no such port").into())
    }
}
