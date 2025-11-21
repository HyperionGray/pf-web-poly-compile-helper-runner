// Rust example - memory safety and debugging
use std::env;

fn calculate_fibonacci(n: u32) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        _ => calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2),
    }
}

fn process_vector(items: &mut Vec<i32>) {
    println!("\n=== Processing Vector ===");
    println!("Original: {:?}", items);
    
    // Double each element
    for item in items.iter_mut() {
        *item *= 2;
    }
    
    println!("Doubled: {:?}", items);
    
    // Calculate sum
    let sum: i32 = items.iter().sum();
    println!("Sum: {}", sum);
}

struct Person {
    name: String,
    age: u32,
}

impl Person {
    fn new(name: &str, age: u32) -> Self {
        Person {
            name: name.to_string(),
            age,
        }
    }
    
    fn greet(&self) {
        println!("Hello, I'm {} and I'm {} years old", self.name, self.age);
    }
}

fn main() {
    println!("=== Debug Practice Program (Rust) ===\n");
    
    let args: Vec<String> = env::args().collect();
    
    if args.len() > 1 {
        println!("Program arguments:");
        for (i, arg) in args.iter().enumerate() {
            println!("  [{}]: {}", i, arg);
        }
    }
    
    // Fibonacci calculation
    println!("\n=== Fibonacci Sequence ===");
    for i in 0..10 {
        let fib = calculate_fibonacci(i);
        println!("F({}) = {}", i, fib);
    }
    
    // Vector processing
    let mut numbers = vec![1, 2, 3, 4, 5];
    process_vector(&mut numbers);
    
    // Struct example
    println!("\n=== Person Example ===");
    let person = Person::new("Alice", 30);
    person.greet();
    
    println!("\n✅ Program completed successfully!");
}
