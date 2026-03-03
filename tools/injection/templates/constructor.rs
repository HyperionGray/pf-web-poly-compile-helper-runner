use std::ffi::c_void;

// Constructor function - executed when library is loaded
#[ctor::ctor]
fn injected_constructor() {
    println!("[INJECTED] Rust constructor executed!");
    // Add your injection code here
}

// Destructor function - executed when library is unloaded
#[ctor::dtor]
fn injected_destructor() {
    println!("[INJECTED] Rust destructor executed!");
    // Add cleanup code here
}

// Example function that can be called from injected code
#[no_mangle]
pub extern "C" fn injected_function() {
    println!("[INJECTED] Rust function called!");
}

// Required for shared library
#[no_mangle]
pub extern "C" fn _start() {}
