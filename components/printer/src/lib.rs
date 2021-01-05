use dlal_component_base::{component, serde_json};

component!(
    {"in": ["audio", "midi", "cmd"], "out": []},
    [
        "audio",
        {"name": "field_helpers", "fields": ["print_audio", "print_midi", "print_cmd"], "kinds": ["rw", "json"]},
    ],
    {
        print_audio: u32,
        print_midi: bool,
        print_cmd: bool,
        run_count: u32,
    },
    {
        "print_audio": {
            "desc": "0 to disable, n to print every nth audio",
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.print_audio = 1000;
        self.print_midi = true;
        self.print_cmd = true;
    }

    fn command(&mut self, body: &serde_json::Value) {
        if self.print_cmd {
            println!("{} got cmd: {}", self.name, serde_json::to_string_pretty(body).unwrap());
        }
    }

    fn run(&mut self) {
        if self.print_audio != 0 {
            self.run_count += 1;
            if self.run_count == self.print_audio {
                print!("{} {}th audio:", self.name, self.run_count);
                for i in &self.audio {
                    print!(" {:.2e}", i);
                }
                println!("");
                self.run_count = 0;
            }
        }
        for i in &mut self.audio {
            *i = 0.0;
        }
    }

    fn midi(&mut self, msg: &[u8]) {
        if self.print_midi {
            println!("{} got midi: {:02x?}", self.name, msg);
        }
    }
}
