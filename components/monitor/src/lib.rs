use dlal_component_base::{component, json_to_ptr, serde_json, Body, CmdResult};

component!(
    {"in": ["cmd"], "out": []},
    [
        "run_size",
        "sample_rate",
        //{"name": "field_helpers", "fields": ["value1"], "kinds": ["rw", "json"]},
    ],
    {
        //value1: f32,
        //value2: f32,
    },
    {
        "stft": {
            "args": [{
                "name": "stft",
                "kind": "norm",
            }],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        //self.value1 = 1.0;
        //self.value2 = 2.0;
    }
}

impl Component {
    fn stft_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let data = json_to_ptr!(body.arg::<serde_json::Value>(0)?, *const f32);
        let len = body.arg(1)?;
        let stft = unsafe { std::slice::from_raw_parts(data, len) };
        println!(
            "{:.5} {:.5} {:.5} {:.5}",
            stft[   1..1024].iter().sum::<f32>(),
            stft[1024..2048].iter().sum::<f32>(),
            stft[2049..3073].iter().sum::<f32>(),
            stft[3073..4096].iter().sum::<f32>(),
        );
        Ok(None)
    }
}
