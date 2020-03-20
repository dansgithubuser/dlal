use portaudio as pa;
use serde_json::Value;

use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_void};
use std::ptr;

const SAMPLE_RATE: f64 = 44_100.0;
const FRAMES: u32 = 64;
const CHANNELS: i32 = 2;
const INTERLEAVED: bool = true;

fn run() -> Result<(), pa::Error> {
    let pa = pa::PortAudio::new()?;

    println!("PortAudio:");
    println!("version: {}", pa.version());
    println!("version text: {:?}", pa.version_text());
    println!("host count: {}", pa.host_api_count()?);

    let default_host = pa.default_host_api()?;
    println!("default host: {:#?}", pa.host_api_info(default_host));

    let def_input = pa.default_input_device()?;
    let input_info = pa.device_info(def_input)?;
    println!("Default input device info: {:#?}", &input_info);

    // Construct the input stream parameters.
    let latency = input_info.default_low_input_latency;
    let input_params = pa::StreamParameters::<f32>::new(def_input, CHANNELS, INTERLEAVED, latency);

    let def_output = pa.default_output_device()?;
    let output_info = pa.device_info(def_output)?;
    println!("Default output device info: {:#?}", &output_info);

    // Construct the output stream parameters.
    let latency = output_info.default_low_output_latency;
    let output_params = pa::StreamParameters::new(def_output, CHANNELS, INTERLEAVED, latency);

    // Check that the stream format is supported.
    pa.is_duplex_format_supported(input_params, output_params, SAMPLE_RATE)?;

    // Construct the settings with which we'll open our duplex stream.
    let settings = pa::DuplexStreamSettings::new(input_params, output_params, SAMPLE_RATE, FRAMES);

    // Once the countdown reaches 0 we'll close the stream.
    let mut count_down = 3.0;

    // Keep track of the last `current_time` so we can calculate the delta time.
    let mut maybe_last_time = None;

    // We'll use this channel to send the count_down to the main thread for fun.
    let (sender, receiver) = ::std::sync::mpsc::channel();

    // A callback to pass to the non-blocking stream.
    let callback = move |pa::DuplexStreamCallbackArgs {
                             in_buffer,
                             out_buffer,
                             frames,
                             time,
                             ..
                         }| {
        let current_time = time.current;
        let prev_time = maybe_last_time.unwrap_or(current_time);
        let dt = current_time - prev_time;
        count_down -= dt;
        maybe_last_time = Some(current_time);

        assert!(frames == FRAMES as usize);
        sender.send(count_down).ok();

        // Pass the input straight to the output - BEWARE OF FEEDBACK!
        for (output_sample, input_sample) in out_buffer.iter_mut().zip(in_buffer.iter()) {
            *output_sample = *input_sample;
        }

        if count_down > 0.0 {
            pa::Continue
        } else {
            pa::Complete
        }
    };

    // Construct a stream with input and output sample types of f32.
    let mut stream = pa.open_non_blocking_stream(settings, callback)?;

    stream.start()?;

    // Loop while the non-blocking stream is active.
    while let true = stream.is_active()? {
        // Do some stuff!
        while let Ok(count_down) = receiver.try_recv() {
            println!("count_down: {:?}", count_down);
        }
    }

    stream.stop()?;

    Ok(())
}

pub struct Component {
    result: CString,
}

impl Component {
    fn set_result(&mut self, new_result: &str) -> *const c_char {
        self.result = CString::new(new_result).expect("CString::new failed");
        self.result.as_ptr()
    }
}

#[no_mangle]
pub extern "C" fn construct() -> *mut Component {
    Box::into_raw(Box::new(Component { result: CString::new("").expect("CString::new failed") }))
}

#[no_mangle]
pub extern "C" fn destruct(component: *mut Component) {
    unsafe { Box::from_raw(component) };
}

#[no_mangle]
pub extern "C" fn command(component: *mut Component, text: *const c_char) -> *const c_char {
    let component = unsafe { &mut *component };
    let body: Value = serde_json::from_str(unsafe { CStr::from_ptr(text) }.to_str().expect("CStr::to_str failed")).expect("invalid command");
    match body["name"].as_str().expect("command name isn't a string") {
        "add" => {
            let raw = body["args"][0].as_str().unwrap().parse::<usize>().unwrap();
            let raw = unsafe { std::mem::transmute::<usize, *mut c_void>(raw) };
            let cmd = body["args"][1].as_str().unwrap().parse::<usize>().unwrap();
            let cmd = unsafe { std::mem::transmute::<usize, extern "C" fn(cmp: *mut c_void, text: *const c_char) -> *const c_char>(cmd) };
            let text = CString::new(r#"{"name": "butts"}"#).unwrap();
            println!("{:?}", unsafe { CStr::from_ptr(cmd(raw, text.as_ptr())) });
            std::ptr::null()
        },
        _ => {
            component.set_result(r#"{"error": "no such command"}"#)
        },
    }
}
