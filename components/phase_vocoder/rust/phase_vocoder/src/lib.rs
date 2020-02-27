extern crate ladspa;
extern crate pvoc_plugins;

use ladspa::Plugin;

use std::os::raw::{c_char, c_void};

#[no_mangle]
pub extern "C" fn construct(
    kind: *const c_char,
    sample_rate: f64,
    bins: u32,
    time_div: u32,
) -> *mut c_void {
    let new = match kind {
        _ => return std::ptr::null_mut(),
    };
    //Box::into_raw(Box::new(.new(1, sample_rate, bins, time_div)));
}

#[no_mangle]
pub unsafe extern "C" fn destruct(plugin: *mut c_void) {
    let _ = Box::from_raw(plugin);
}

#[no_mangle]
pub extern "C" fn run(plugin: *mut c_void, audio: *mut f32, size: u32) {
}
