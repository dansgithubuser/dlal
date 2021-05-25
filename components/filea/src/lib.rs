use dlal_component_base::{component, err, json, serde_json, Body, CmdResult};

component!(
    {"in": [""], "out": ["audio"]},
    [
        "run_size",
        "sample_rate",
        "uni",
        "check_audio",
    ],
    {
        reader: Option<claxon::FlacReader<std::fs::File>>,
        block: Vec<f32>,
        block_i: usize,
        buffer: Vec<i32>,
    },
    {
        "open": {
            "args": ["file path"],
        },
        "duration": {
            "args": [],
            "return": "number of samples",
        },
    },
);

impl ComponentTrait for Component {
    fn run(&mut self) {
        let reader = match &mut self.reader {
            Some(v) => v,
            None => return,
        };
        let output = match &self.output {
            Some(v) => v,
            None => return,
        };
        let audio = output.audio(self.run_size).unwrap();
        for i in 0..self.run_size {
            if self.block_i == self.block.len() {
                self.block = match reader.blocks().read_next_or_eof(vec![]) {
                    Ok(Some(block)) => {
                        (0..block.duration())
                            .map(|i| block.sample(0, i) as f32 / 0x8000 as f32)
                            .collect()
                    }
                    _ => return,
                };
                self.block_i = 0;
            }
            audio[i] += self.block[self.block_i];
            self.block_i += 1;
        }
    }
}

impl Component {
    fn open_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let file_path: String = body.arg(0)?;
        self.reader = match claxon::FlacReader::open(&file_path) {
            Ok(v) => Some(v),
            Err(e) => return Err(err!("{:?}", e).into()),
        };
        Ok(None)
    }

    fn duration_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        let reader = match &self.reader {
            Some(v) => v,
            None => return Err(err!("No file opened.").into()),
        };
        let samples = match reader.streaminfo().samples {
            Some(v) => v,
            None => return Err(err!("No samples.").into()),
        };
        Ok(Some(json!(samples)))
    }
}
