(module
  ;; Import functions from the host environment
  (import "env" "log" (func $log (param i32)))
  
  ;; Memory for hook data
  (memory (export "memory") 1)
  
  ;; Hook function that wraps another function
  (func $hook_wrapper (param $value i32) (result i32)
    ;; Log the input
    local.get $value
    call $log
    
    ;; Do some processing
    local.get $value
    i32.const 1
    i32.add
    
    ;; Return modified value
  )
  
  (export "hook_wrapper" (func $hook_wrapper))
)
