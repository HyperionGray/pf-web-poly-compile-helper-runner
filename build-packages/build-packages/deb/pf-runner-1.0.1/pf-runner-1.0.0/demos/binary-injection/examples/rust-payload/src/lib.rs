use std::ffi::CString;
use libc::{getpid, printf};

// Constructor function - executed when library is loaded
#[ctor::ctor]
fn injected_constructor() {
    println!("[INJECTED] Rust payload constructor executed!");
    unsafe {
        let pid = getpid();
        println!("[INJECTED] Process PID: {}", pid);
    }
    println!("[INJECTED] Rust injection successful!");
}

// Destructor function - executed when library is unloaded
#[ctor::dtor]
fn injected_destructor() {
    println!("[INJECTED] Rust payload destructor executed!");
}

// Example function that can be called from injected code
#[no_mangle]
pub extern "C" fn injected_rust_function() -> i32 {
    println!("[INJECTED] Rust function called from injection!");
    42
}

// Example of calling C functions from Rust injection
#[no_mangle]
pub extern "C" fn rust_call_c_function() {
    unsafe {
        let message = CString::new("[INJECTED] Message from Rust calling C printf\n").unwrap();
        printf(message.as_ptr());
    }
}

// Example of a more complex injection that could hook functions
#[no_mangle]
pub extern "C" fn rust_injection_hook() {
    println!("[INJECTED] Rust hook function executed!");
    
    // Example: Log some information about the process
    unsafe {
        let pid = getpid();
        println!("[INJECTED] Current process PID from Rust: {}", pid);
    }
    
    // You could add more sophisticated hooking logic here
    // For example, intercepting function calls, modifying behavior, etc.
}