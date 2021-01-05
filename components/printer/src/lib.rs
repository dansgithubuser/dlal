use dlal_component_base::{component, json, serde_json, Body, CmdResult};

component!(
    {"in": ["audio", "midi", "cmd"], "out": []},
    ["audio"],
    {
        print_audio: u32,
        print_midi: bool,
        print_cmd: bool,
        run_count: u32,
    },
    {},
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.print_audio = 1000;
        self.print_midi = true;
        self.print_cmd = true;
        self.run_count = 0;
    }

    fn command(&mut self, body: &serde_json::Value) {
        println!("{} got cmd: {}", self.name, serde_json::to_string_pretty(body).unwrap());
    }

    fn run(&mut self) {
        self.run_count += 1;
        if self.run_count == self.print_audio {
            print!("{} {}th audio:", self.name, self.run_count);
            for i in &self.audio {
                print!(" {:.2e}", i);
            }
            println!("");
            self.run_count = 0;
        }
        for i in &mut self.audio {
            *i = 0.0;
        }
    }

    fn midi(&mut self, msg: &[u8]) {
        println!("{} got midi: {:02x?}", self.name, msg);
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(json!({
            "print_audio": self.print_audio,
            "print_midi": self.print_midi,
            "print_cmd": self.print_cmd,
        })))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = body.arg::<serde_json::Value>(0)?;
        self.print_audio = j.at("print_audio")?;
        self.print_midi = j.at("print_midi")?;
        self.print_cmd = j.at("print_cmd")?;
        Ok(None)
    }
}
