/*
The YM2612 has:
- 6 monophonic voices
- four FM operators per voice

We have:
- A single polyphonic voice
- four FM operators

As such, while the hardware operators were also the osillators, we take the
operator to be the house of operator configuration, and invent "runners" which
are the product of notes and operators, and is responsible for the actual FM.
*/

const OPS: usize = 4;
const NOTES: usize = 128;

fn wave(phase: f32) -> f32 {
    (phase * 2.0 * std::f32::consts::PI).sin()
}

// ===== runner ===== //
enum Stage {
    A, //attack
    D, //decay
    S, //sustain
    R, //release
}

impl Default for Stage {
    fn default() -> Self {
        Stage::R
    }
}

#[derive(Default)]
struct Runner {
    stage: Stage,
    phase: f32,
    step: f32, //amount to advance phase without FM
    vol: f32,  //current volume, aka envelope, evolves according to ADSR config
    amp: f32,  //current output amplitude
}

impl Runner {
    fn start(&mut self, zero: bool) {
        self.stage = Stage::A;
        if zero {
            self.vol = 0.0;
        }
    }

    fn advance(&mut self, m: f32) {
        self.phase += self.step * m;
        self.phase -= (self.phase as u32) as f32;
    }
}

// ===== operator ===== //
struct Op {
    a: f32,
    d: f32,
    s: f32,
    r: f32,
    m: f32,
    i: [f32; OPS],
    o: f32,
}

impl Op {
    // return true if the runner is done
    fn advance(&self, runner: &mut Runner, m: f32) -> bool {
        runner.advance(m);
        match runner.stage {
            Stage::A => {
                runner.vol += self.a;
                if runner.vol > 1.0 {
                    runner.vol = 1.0;
                    runner.stage = Stage::D;
                }
            }
            Stage::D => {
                runner.vol -= self.d;
                if runner.vol < self.s {
                    runner.vol = self.s;
                    runner.stage = Stage::S;
                }
            }
            Stage::S => (),
            Stage::R => {
                runner.vol -= self.r;
                if runner.vol < 0.0 {
                    runner.vol = 0.0;
                    return true;
                }
            }
        }
        self.o == 0.0
    }
}

impl Default for Op {
    fn default() -> Self {
        Self {
            a: 0.01,
            d: 0.01,
            s: 0.5,
            r: 0.01,
            m: 1.0,
            i: [0.0, 0.0, 0.0, 0.0],
            o: 0.0,
        }
    }
}

// ===== note ===== //
#[derive(Default)]
struct Note {
    runners: [Runner; OPS],
    vol: f32,   //current volume
    vol_f: f32, //volume requested by performer
    done: bool,
}

impl Note {
    fn set(&mut self, frequency: f32, sample_rate: u32, ops: &[Op]) {
        if sample_rate == 0 {
            return;
        }
        let step = frequency / sample_rate as f32;
        for (i, op) in ops.iter().enumerate() {
            self.runners[i].step = step * op.m;
        }
    }

    fn start(&mut self, vol: f32) {
        for runner in &mut self.runners {
            runner.start(self.done);
        }
        self.vol = vol;
        self.vol_f = vol;
        self.done = false;
    }

    fn stop(&mut self) {
        for runner in &mut self.runners {
            runner.stage = Stage::R;
        }
    }

    fn advance(&mut self, index: usize, ops: &[Op], m: f32) -> f32 {
        self.vol = (63.0 * self.vol + self.vol_f) / 64.0;
        self.done &= ops[index].advance(&mut self.runners[index], m);
        let mut modulated_phase = self.runners[index].phase;
        for i in 0..OPS {
            modulated_phase += self.runners[i].amp * ops[index].i[i];
        }
        self.runners[index].amp = wave(modulated_phase) * self.runners[index].vol;
        self.runners[index].amp * ops[index].o * self.vol
    }
}

// ===== component ===== //
macro_rules! op_command {
    ($commands:ident, $name:literal, $type:ty, ($($member:tt)+), ($($info:tt)+), $set:expr) => {
        command!(
            $commands,
            $name,
            |soul, body| {
                let op: usize = arg_num(&body, 0)?;
                if let Ok(v) = arg_num::<$type>(&body, 1) {
                    soul.ops[op].$($member)+ = v;
                }
                if ($set) {
                    soul.set(soul.m);
                }
                Ok(Some(json!(soul.ops[op].$($member)+.to_string())))
            },
            {"args": ["operator", $($info)+]},
        );
    }
}

use dlal_component_base::{
    arg, arg_num, command, gen_component, join, json, json_get, json_num, uni, JsonValue, View,
};

use std::collections::HashMap;
use std::f32;

#[derive(Default)]
pub struct Specifics {
    ops: [Op; OPS],
    notes: Vec<Note>,
    m: f32,                //bend amount
    rpn: u16,              //registered parameter number
    pitch_bend_range: f32, //MIDI RPN 0x0000
    samples_per_evaluation: usize,
    sample_rate: u32,
    output: Option<View>,
}

impl Specifics {
    fn set(&mut self, m: f32) {
        self.m = m;
        for i in 0..self.notes.len() {
            let f = 440.0 * (2.0 as f32).powf((i as f32 - 69.0) / 12.0);
            self.notes[i].set(f, self.sample_rate, &self.ops);
        }
    }
}

gen_component!(Specifics);

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        let mut result = Specifics {
            pitch_bend_range: 2.0,
            ..Default::default()
        };
        result.ops[0].o = 0.25;
        result.notes.resize_with(NOTES, || Note {
            done: true,
            ..Default::default()
        });
        result
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                join!(samples_per_evaluation soul, body);
                join!(sample_rate soul, body);
                soul.set(1.0);
                Ok(None)
            },
            ["samples_per_evaluation", "sample_rate"],
        );
        uni!(connect commands, true);
        op_command!(commands, "a", f32, (a), ({
            "name": "amount",
            "desc": "attack rate",
            "units": "amplitude per sample",
            "range": "(0, 1]",
        }), false);
        op_command!(commands, "d", f32, (d), ({
            "name": "amount",
            "desc": "decay rate",
            "units": "amplitude per sample",
            "range": "(0, 1]",
        }), false);
        op_command!(commands, "s", f32, (s), ({
            "name": "amount",
            "desc": "sustain level",
            "range": "[0, 1]",
        }), false);
        op_command!(commands, "r", f32, (r), ({
            "name": "amount",
            "desc": "release rate",
            "units": "amplitude per sample",
            "range": "(0, 1]",
        }), false);
        op_command!(commands, "m", f32, (m), ({
            "name": "amount",
            "desc": "frequency multiplier",
        }), true);
        op_command!(commands, "i0", f32, (i[0]), ({
            "name": "amount",
            "desc": "FM from operator 0",
        }), false);
        op_command!(commands, "i1", f32, (i[1]), ({
            "name": "amount",
            "desc": "FM from operator 1",
        }), false);
        op_command!(commands, "i2", f32, (i[2]), ({
            "name": "amount",
            "desc": "FM from operator 2",
        }), false);
        op_command!(commands, "i3", f32, (i[3]), ({
            "name": "amount",
            "desc": "FM from operator 3",
        }), false);
        op_command!(commands, "o", f32, (o), ({
            "name": "amount",
            "desc": "amount to contribute to output",
            "range": "[0, 1]",
        }), false);
        command!(
            commands,
            "to_json",
            |soul, _body| {
                let mut ops = HashMap::<String, JsonValue>::new();
                for (i, op) in soul.ops.iter().enumerate() {
                    ops.insert(
                        i.to_string(),
                        json!({
                            "a": op.a,
                            "d": op.d,
                            "s": op.s,
                            "r": op.r,
                            "m": op.m,
                            "i0": op.i[0],
                            "i1": op.i[1],
                            "i2": op.i[2],
                            "i3": op.i[3],
                            "o": op.o,
                        }),
                    );
                }
                Ok(Some(json!(ops)))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                let j = arg(&body, 0)?;
                for i in 0..OPS {
                    let op = json_get(j, &i.to_string())?;
                    soul.ops[i].a = json_num(json_get(op, "a")?)?;
                    soul.ops[i].d = json_num(json_get(op, "d")?)?;
                    soul.ops[i].s = json_num(json_get(op, "s")?)?;
                    soul.ops[i].r = json_num(json_get(op, "r")?)?;
                    soul.ops[i].m = json_num(json_get(op, "m")?)?;
                    soul.ops[i].i[0] = json_num(json_get(op, "i0")?)?;
                    soul.ops[i].i[1] = json_num(json_get(op, "i1")?)?;
                    soul.ops[i].i[2] = json_num(json_get(op, "i2")?)?;
                    soul.ops[i].i[3] = json_num(json_get(op, "i3")?)?;
                    soul.ops[i].o = json_num(json_get(op, "o")?)?;
                }
                soul.set(1.0);
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn midi(&mut self, msg: &[u8]) {
        if msg.is_empty() {
            return;
        }
        match msg[0] & 0xf0 {
            0x80 => {
                if msg.len() >= 3 {
                    self.notes[msg[1] as usize].stop();
                }
            }
            0x90 => {
                if msg.len() >= 3 {
                    if msg[2] == 0 {
                        self.notes[msg[1] as usize].stop();
                    } else {
                        self.notes[msg[1] as usize].start(msg[2] as f32 / 127.0);
                    }
                }
            }
            0xa0 => {
                if msg.len() >= 3 {
                    self.notes[msg[1] as usize].vol_f = msg[2] as f32 / 127.0;
                }
            }
            0xb0 => {
                if msg.len() >= 3 {
                    match msg[1] {
                        0x65 => self.rpn = (msg[2] << 7) as u16,
                        0x64 => self.rpn += msg[2] as u16,
                        0x06 => match self.rpn {
                            0x0000 => self.pitch_bend_range = msg[2] as f32,
                            _ => (),
                        },
                        0x26 => match self.rpn {
                            0x0000 => self.pitch_bend_range += msg[2] as f32 / 100.0,
                            _ => (),
                        },
                        _ => (),
                    }
                }
            }
            0xe0 => {
                if msg.len() >= 3 {
                    const CENTER: f32 = 0x2000 as f32;
                    let value = (msg[1] as u16 + ((msg[2] as u16) << 7)) as f32;
                    let octaves = self.pitch_bend_range * (value - CENTER) / (CENTER * 12.0);
                    self.set((2.0 as f32).powf(octaves));
                }
            }
            _ => (),
        };
    }

    fn evaluate(&mut self) {
        let audio = match &self.output {
            Some(output) => output.audio(self.samples_per_evaluation).unwrap(),
            None => return,
        };
        for note in &mut self.notes {
            if note.done {
                continue;
            }
            for i in audio.iter_mut() {
                note.done = true;
                for op in 0..OPS {
                    *i += note.advance(op, &self.ops, self.m);
                }
            }
        }
    }
}
