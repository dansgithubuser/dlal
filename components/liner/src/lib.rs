use dlal_component_base::{component, err, json, serde_json, Arg, Body, CmdResult, View};

use multiqueue2::{MPMCSender, MPMCUniReceiver};
use serde::{ser::SerializeSeq, Deserialize, Serialize, Serializer};

use std::error::Error as StdError;

#[derive(Clone, Debug, Deserialize)]
enum Msg {
    Short([u8; 3]),
    Long(Vec<u8>),
}

impl Msg {
    fn new(msg: &serde_json::Value) -> Result<Self, Box<dyn StdError>> {
        let array = msg.to::<Vec<_>>()?;
        Ok(if array.len() <= 3 {
            let mut msg = [0, 0, 0];
            msg[..array.len()].clone_from_slice(&array);
            Msg::Short(msg)
        } else {
            Msg::Long(array)
        })
    }

    fn as_slice(&self) -> &[u8] {
        match self {
            Msg::Short(msg) => msg,
            Msg::Long(msg) => msg.as_slice(),
        }
    }
}

impl Serialize for Msg {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let slice = self.as_slice();
        let mut seq = serializer.serialize_seq(Some(slice.len()))?;
        for i in slice {
            seq.serialize_element(i)?;
        }
        seq.end()
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct Deltamsg {
    delta: u32,
    msg: Msg,
}

impl Deltamsg {
    fn new(deltamsg: &serde_json::Value) -> Result<Self, Box<dyn StdError>> {
        Ok(Self {
            delta: deltamsg.at("delta")?,
            msg: Msg::new(&deltamsg.at("msg")?)?,
        })
    }
}

#[derive(Debug, Default, Serialize, Deserialize)]
struct Line {
    deltamsgs: Vec<Deltamsg>,
    ticks_per_quarter: u32,
    us_per_quarter: u32,
    index: usize, //used to convey which line this is, and then to keep track of current deltamsg
    samples_ere_last_tempo: u32,
    ticks_aft_last_tempo: u32,
    offset: f64,
}

impl Line {
    fn new(
        deltamsgs: &serde_json::Value,
        ticks_per_quarter: u32,
        index: usize,
    ) -> Result<Self, Box<dyn StdError>> {
        let mut r = Self {
            deltamsgs: deltamsgs.to::<Vec<_>>()?.vec_map(|i| Deltamsg::new(&i))?,
            ticks_per_quarter,
            index,
            ..Default::default()
        };
        r.reset();
        Ok(r)
    }

    fn advance(
        &mut self,
        samples: u32,
        run_size: usize,
        sample_rate: u32,
        output: Option<&View>,
        mut msgs: Option<&mut Vec<Vec<u8>>>,
    ) -> bool {
        let mut delta = self.calculate_delta(samples, sample_rate);
        loop {
            // if there's nothing left in the line, we're done
            if self.index >= self.deltamsgs.len() {
                return true;
            }
            // if we haven't passed a msg, return
            let deltamsg = &self.deltamsgs[self.index];
            if deltamsg.delta > delta {
                return false;
            }
            // handle a msg
            let msg = deltamsg.msg.as_slice();
            if msg[0] == 0xff && msg[1] == 0x51 {
                // keep track of tempo changes
                self.us_per_quarter =
                    ((msg[3] as u32) << 16) + ((msg[4] as u32) << 8) + msg[5] as u32;
                self.samples_ere_last_tempo = samples - run_size as u32;
                self.ticks_aft_last_tempo = 0;
            } else {
                // count ticks since last tempo
                self.ticks_aft_last_tempo += deltamsg.delta;
            }
            if let Some(output) = output {
                output.midi(msg);
            }
            if let Some(msgs) = &mut msgs {
                msgs.push(msg.to_vec());
            }
            // prepare for next
            delta -= deltamsg.delta; // reduce delta we owe by how far we advanced
            self.index += 1; // next msg
        }
    }

    fn reset(&mut self) {
        self.us_per_quarter = 500_000;
        self.index = 0;
        self.ticks_aft_last_tempo = 0;
    }

    fn calculate_delta(&self, samples: u32, sample_rate: u32) -> u32 {
        const US_PER_S: f64 = 1e6;
        let ticks_per_us = self.ticks_per_quarter as f64 / self.us_per_quarter as f64;
        let ticks_per_s = ticks_per_us * US_PER_S;
        let ticks_per_sample = ticks_per_s / sample_rate as f64;
        let samples_aft_last_tempo =
            samples as f64 - self.offset * sample_rate as f64 - self.samples_ere_last_tempo as f64;
        if samples_aft_last_tempo < 0.0 {
            return 0;
        }
        let ticks_aft_last_tempo = (ticks_per_sample * samples_aft_last_tempo as f64) as u32;
        if self.ticks_aft_last_tempo > ticks_aft_last_tempo {
            return 0;
        }
        ticks_aft_last_tempo - self.ticks_aft_last_tempo
    }

    fn get_notes(&self, run_size: usize, sample_rate: u32) -> serde_json::Value {
        let mut copy = Self {
            deltamsgs: self.deltamsgs.clone(),
            ticks_per_quarter: self.ticks_per_quarter,
            ..Default::default()
        };
        copy.reset();
        let mut samples = 0;
        let mut notes = vec![];
        let mut done = false;
        while !done {
            samples += run_size as u32;
            let mut msgs: Vec<Vec<u8>> = vec![];
            done = copy.advance(samples, run_size, sample_rate, None, Some(&mut msgs));
            for msg in msgs {
                if msg[0] & 0xe0 != 0x80 {
                    // not related to notes
                    continue;
                }
                if msg[0] & 0xf0 == 0x90 && msg[2] != 0 {
                    // note on
                    notes.push(json!({
                        "on": samples,
                        "number": msg[1],
                        "velocity_on": msg[2],
                    }));
                } else {
                    // note off
                    for note in &mut notes {
                        if note.get("number").unwrap() == msg[1] && note.get("off").is_none() {
                            note["off"] = json!(samples);
                            note["velocity_off"] = json!(msg[2]);
                        }
                    }
                }
            }
        }
        json!(notes)
    }
}

struct Queue {
    send: MPMCSender<Box<Line>>,
    recv: MPMCUniReceiver<Box<Line>>,
}

impl Default for Queue {
    fn default() -> Self {
        let (send, recv) = multiqueue2::mpmc_queue(16);
        Self {
            send,
            recv: recv.into_single().expect("into_single failed"),
        }
    }
}

component!(
    {"in": ["midi*"], "out": ["midi"]},
    [
        "run_size",
        "sample_rate",
        {"name": "connect_info", "args": "view", "flavor": "multi"},
        {"name": "disconnect_info", "args": "view", "flavor": "multi"},
    ],
    {
        queue: Queue,
        lines: Vec<Box<Line>>,
        samples: u32,
        outputs: Vec<Option<View>>,
    },
    {
        "get_midi": {
            "args": ["line_index"],
            "return": {
                "ticks_per_quarter": "number",
                "deltamsgs": "[{delta, msg}, ..]",
            },
        },
        "get_midi_all": {
            "return": [{
                "ticks_per_quarter": "number",
                "deltamsgs": "[{delta, msg}, ..]",
            }],
        },
        "set_midi": {
            "args": [
                "line_index",
                "ticks_per_quarter",
                {
                    "name": "deltamsgs",
                    "desc": "[{delta, msg}, ..]",
                },
            ],
            "kwargs": [{
                "name": "immediate",
                "default": false,
                "desc": "immediately enact the line after loading",
            }],
        },
        "get_notes": {
            "args": ["line_index"],
            "return": "[{on, off, number, velocity_on, velocity_off}, ..]",
            "desc": "on and off are measured in samples; off and velocity_off may be missing",
        },
        "offset": {"args": ["line_index", "seconds"]},
        "advance": {"args": ["seconds"]},
        "skip_line": {"args": [{"desc": "number of lines", "default": 1}]},
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.run_size = 64;
        self.sample_rate = 44100;
        self.outputs.reserve(16);
        for _ in 0..16 {
            self.lines.push(Box::new(Line::default()));
        }
    }

    fn connect(&mut self, body: serde_json::Value) -> CmdResult {
        let output = View::new(&body.at("args")?)?;
        self.outputs.push(Some(output));
        Ok(None)
    }

    fn disconnect(&mut self, body: serde_json::Value) -> CmdResult {
        let output = View::new(&body.at("args")?)?;
        if let Some(i) = self
            .outputs
            .iter()
            .position(|i| i.as_ref() == Some(&output))
        {
            self.outputs[i] = None;
        }
        Ok(None)
    }

    fn run(&mut self) {
        while let Ok(mut line) = self.queue.recv.try_recv() {
            let line_index = (*line).index;
            (*line).index = (*self.lines[line_index]).index;
            self.lines[line_index] = line;
        }
        self.samples += self.run_size as u32;
        let mut done = true;
        for i in 0..self.lines.len() {
            done &= self.lines[i].advance(
                self.samples,
                self.run_size,
                self.sample_rate,
                if i >= self.outputs.len() {
                    None
                } else {
                    self.outputs[i].as_ref()
                },
                None,
            );
        }
        if done {
            self.samples = 0;
            for line in &mut self.lines {
                line.reset();
            }
        }
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({ "lines": self.lines })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = body.arg::<serde_json::Value>(0)?;
        let lines = j.at::<Vec<serde_json::Value>>("lines")?;
        for i in 0..lines.len() {
            self.lines[i] = serde_json::from_str(&lines[i].to_string())?;
        }
        Ok(None)
    }
}

impl Component {
    fn get_midi_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let line_index: usize = body.arg(0)?;
        if line_index >= self.lines.len() {
            return Err(err!(
                "got line_index {} but number of lines is only {}",
                line_index,
                self.lines.len()
            )
            .into());
        }
        let line = &self.lines[line_index];
        Ok(Some(json!({
            "ticks_per_quarter": line.ticks_per_quarter,
            "deltamsgs": line.deltamsgs,
        })))
    }

    fn get_midi_all_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!(self
            .lines
            .iter()
            .map(|line| json!({
                "ticks_per_quarter": line.ticks_per_quarter,
                "deltamsgs": line.deltamsgs,
            }))
            .collect::<Vec<_>>())))
    }

    fn set_midi_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let line_index: usize = body.arg(0)?;
        let ticks_per_quarter: u32 = body.arg(1)?;
        let deltamsgs = body.arg(2)?;
        if line_index >= self.lines.len() {
            return Err(err!(
                "got line_index {} but number of lines is only {}",
                line_index,
                self.lines.len()
            )
            .into());
        }
        if let Ok(immediate) = body.kwarg("immediate") {
            if immediate {
                self.lines[line_index] = Box::new(Line::new(
                    &deltamsgs,
                    ticks_per_quarter,
                    self.lines[line_index].index,
                )?);
                return Ok(None);
            }
        }
        self.queue.send.try_send(Box::new(Line::new(
            &deltamsgs,
            ticks_per_quarter,
            line_index,
        )?))?;
        Ok(None)
    }

    fn get_notes_cmd(&self, body: serde_json::Value) -> CmdResult {
        let line_index: usize = body.arg(0)?;
        if line_index >= self.lines.len() {
            return Err(err!(
                "got line_index {} but number of lines is only {}",
                line_index,
                self.lines.len()
            )
            .into());
        }
        Ok(Some(
            self.lines[line_index].get_notes(self.run_size, self.sample_rate),
        ))
    }

    fn offset_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let line_index: usize = body.arg(0)?;
        let seconds: f64 = body.arg(1)?;
        if line_index >= self.lines.len() {
            return Err(err!("invalid line_index").into());
        }
        self.lines[line_index].offset = seconds;
        Ok(None)
    }

    fn advance_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let seconds: f32 = body.arg(0)?;
        let runs_per_second = self.sample_rate as f32 / self.run_size as f32;
        let runs = (seconds * runs_per_second) as u32;
        for _ in 0..runs {
            self.run();
        }
        Ok(None)
    }

    fn skip_line_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let n: usize = body.arg(0)?;
        for _ in 0..n {
            self.outputs.push(None);
        }
        Ok(None)
    }
}
