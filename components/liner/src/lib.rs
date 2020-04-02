use dlal_component_base::{
    arg, arg_num, args, command, err, gen_component, join, JsonValue, View, VIEW_ARGS,
};

use multiqueue2::{MPMCSender, MPMCUniReceiver};

use std::error::Error;
use std::vec::Vec;

#[derive(Debug)]
enum Msg {
    Short([u8; 3]),
    Long(Vec<u8>),
}

impl Msg {
    fn new(msg: &JsonValue) -> Result<Self, Box<dyn Error>> {
        let array = msg
            .as_array()
            .ok_or_else(|| err!(box "msg isn't an array"))?;
        Ok(if array.len() <= 3 {
            let mut msg = [0, 0, 0];
            for i in 0..array.len() {
                msg[i] = array[i]
                    .as_str()
                    .ok_or_else(|| err!(box "byte isn't a string"))?
                    .parse()?;
            }
            Msg::Short(msg)
        } else {
            let mut msg = Vec::new();
            for i in 0..array.len() {
                msg.push(
                    array[i]
                        .as_str()
                        .ok_or_else(|| err!(box "byte isn't a string"))?
                        .parse()?,
                );
            }
            Msg::Long(msg)
        })
    }

    fn as_slice(&self) -> &[u8] {
        match self {
            Msg::Short(msg) => msg,
            Msg::Long(msg) => msg.as_slice(),
        }
    }
}

#[derive(Debug)]
struct Deltamsg {
    delta: u32,
    msg: Msg,
}

impl Deltamsg {
    fn new(deltamsg: &JsonValue) -> Result<Self, Box<dyn Error>> {
        Ok(Self {
            delta: deltamsg
                .get("delta")
                .ok_or_else(|| err!(box "missing delta"))?
                .as_str()
                .ok_or_else(|| err!(box "delta isn't a string"))?
                .parse()?,
            msg: Msg::new(deltamsg.get("msg").ok_or_else(|| err!(box "missing msg"))?)?,
        })
    }
}

#[derive(Debug, Default)]
struct Line {
    deltamsgs: Vec<Deltamsg>,
    ticks_per_quarter: u32,
    us_per_quarter: u32,
    index: usize, //used to convey which line this is, and then to keep track of current deltamsg
    samples_ere_last_tempo: u32,
    ticks_aft_last_tempo: u32,
}

impl Line {
    fn new(
        deltamsgs: &JsonValue,
        ticks_per_quarter: u32,
        index: usize,
    ) -> Result<Self, Box<dyn Error>> {
        let array = deltamsgs
            .as_array()
            .ok_or_else(|| err!(box "deltamsgs isn't an array"))?;
        let mut deltamsgs = Vec::<Deltamsg>::new();
        for deltamsg in array {
            deltamsgs.push(Deltamsg::new(deltamsg)?);
        }
        Ok(Self {
            deltamsgs,
            ticks_per_quarter,
            us_per_quarter: 500_000,
            index,
            ..Default::default()
        })
    }

    fn advance(
        &mut self,
        samples: u32,
        samples_per_evaluation: usize,
        sample_rate: u32,
        output: Option<&View>,
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
                // we handle tempo
                self.us_per_quarter =
                    ((msg[3] as u32) << 16) + ((msg[4] as u32) << 8) + msg[5] as u32;
                self.samples_ere_last_tempo = samples - samples_per_evaluation as u32;
                self.ticks_aft_last_tempo = 0;
            } else {
                // other msgs get forwarded
                if let Some(output) = output {
                    output.midi(msg);
                }
                self.ticks_aft_last_tempo += deltamsg.delta; // count ticks since last tempo
            }
            // prepare for next
            delta -= deltamsg.delta; // reduce delta we owe by how far we advanced
            self.index += 1; // next msg
        }
    }

    fn reset(&mut self) {
        self.index = 0;
        self.ticks_aft_last_tempo = 0;
    }

    fn calculate_delta(&self, samples: u32, sample_rate: u32) -> u32 {
        const US_PER_S: f64 = 1e6;
        let ticks_per_us = self.ticks_per_quarter as f64 / self.us_per_quarter as f64;
        let ticks_per_s = ticks_per_us * US_PER_S;
        let ticks_per_sample = ticks_per_s / sample_rate as f64;
        let samples_aft_last_tempo = samples - self.samples_ere_last_tempo;
        let ticks_aft_last_tempo = (ticks_per_sample * samples_aft_last_tempo as f64) as u32;
        ticks_aft_last_tempo - self.ticks_aft_last_tempo
    }
}

pub struct Specifics {
    samples_per_evaluation: usize,
    sample_rate: u32,
    send: MPMCSender<Box<Line>>,
    recv: MPMCUniReceiver<Box<Line>>,
    lines: Vec<Box<Line>>,
    samples: u32,
    outputs: Vec<Option<View>>,
}

gen_component!(Specifics);

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        let (send, recv) = multiqueue2::mpmc_queue(16);
        let mut lines = Vec::new();
        for _ in 0..16 {
            lines.push(Box::new(Line::default()));
        }
        Self {
            samples_per_evaluation: 0,
            sample_rate: 44100,
            send,
            recv: recv.into_single().expect("into_single failed"),
            lines,
            samples: 0,
            outputs: Vec::with_capacity(16),
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                join!(samples_per_evaluation soul, body);
                join!(sample_rate soul, body);
                Ok(None)
            },
            ["samples_per_evaluation", "sample_rate"],
        );
        command!(
            commands,
            "connect",
            |soul, body| {
                let output = View::new(args(&body)?)?;
                soul.outputs.push(Some(output));
                Ok(None)
            },
            { "args": VIEW_ARGS },
        );
        command!(
            commands,
            "disconnect",
            |soul, body| {
                let output = View::new(args(&body)?)?;
                if let Some(i) = soul
                    .outputs
                    .iter()
                    .position(|i| i.as_ref() == Some(&output))
                {
                    soul.outputs[i] = None;
                }
                Ok(None)
            },
            { "args": VIEW_ARGS },
        );
        command!(
            commands,
            "load_midi",
            |soul, body| {
                let line_index: usize = arg_num(&body, 0)?;
                let ticks_per_quarter: u32 = arg_num(&body, 1)?;
                let deltamsgs = arg(&body, 2)?;
                if line_index >= soul.lines.len() {
                    return err!("got line_index {} but number of lines is only {}", line_index, soul.lines.len());
                }
                soul.send.try_send(Box::new(Line::new(deltamsgs, ticks_per_quarter, line_index)?))?;
                Ok(None)
            },
            {
                "args": [
                    "line_index",
                    "ticks_per_quarter",
                    {
                        "name": "deltamsgs",
                        "desc": "[{delta, msg: [..]}, ..]",
                    },
                ],
            },
        );
        command!(
            commands,
            "advance",
            |soul, body| {
                let seconds: f32 = arg_num(&body, 0)?;
                let evaluations_per_second = soul.sample_rate as f32 / soul.samples_per_evaluation as f32;
                let evaluations = (seconds * evaluations_per_second) as u32;
                for _ in 0..evaluations {
                    soul.evaluate();
                }
                Ok(None)
            },
            {
                "args": ["seconds"],
            },
        );
    }

    fn evaluate(&mut self) {
        while let Ok(mut line) = self.recv.try_recv() {
            let line_index = (*line).index;
            (*line).index = (*self.lines[line_index]).index;
            self.lines[line_index] = line;
        }
        self.samples += self.samples_per_evaluation as u32;
        let mut done = true;
        for i in 0..self.lines.len() {
            done &= self.lines[i].advance(
                self.samples,
                self.samples_per_evaluation,
                self.sample_rate,
                if i >= self.outputs.len() {
                    None
                } else {
                    self.outputs[i].as_ref()
                },
            );
        }
        if done {
            self.samples = 0;
            for line in &mut self.lines {
                line.reset();
            }
        }
    }
}
