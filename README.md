# 8085 Microprocessor Simulator

An interactive web-based simulator for the Intel 8085 microprocessor with real-time visualization of data flow, machine cycles, and control signals.

![8085 Simulator](https://img.shields.io/badge/8085-Simulator-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Flask](https://img.shields.io/badge/Flask-2.0+-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- *Interactive Block Diagram*: Complete architectural representation with ALU, registers (A, B, C, D, E, H, L), Program Counter, Stack Pointer, Control Unit, and Memory
- *Real-Time Data Flow*: Watch data flow through wires and buses with animated particles and glowing effects
- *Machine Cycle Visualization*: Live T-state tracking with control signals (IO/M̅, S1, S0, ALE, RD̅, WR̅)
- *Assembly Code Editor*: Write and validate 8085 assembly language programs
- *Step-by-Step Execution*: Execute instructions one at a time with detailed visualization
- *Live Register Updates*: Register contents and flags displayed directly on component blocks
- *Timing Diagrams*: Real-time clock waveforms and machine cycle analysis

## Screenshots
![WhatsApp Image 2025-11-08 at 17 07 14_91b78bc0](https://github.com/user-attachments/assets/f957bcd8-de32-464f-943e-30b815562b44)


## Supported Instructions

| Category | Instructions |
|----------|-------------|
| Data Transfer | MOV, MVI, LDA, STA, LHLD, SHLD, LXI |
| Arithmetic | ADD, ADI, SUB, SUI, INR, DCR |
| Logical | (Coming soon) |
| Branch | JMP, JZ, JNZ, CALL, RET |
| Stack | PUSH, POP |
| Control | HLT, NOP |

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository
bash
git clone https://github.com/yourusername/8085-simulator.git
cd 8085-simulator


2. Install dependencies
bash
pip install flask flask-socketio


3. Run the application
bash
python app.py


4. Open your browser and navigate to

http://localhost:5000


## Usage

### Writing Assembly Code

Write your 8085 assembly code in the editor. Example:

assembly
MVI A, 0AH        ; Load 0AH into accumulator
MVI B, 05H        ; Load 05H into register B
ADD B             ; Add B to A
STA 2050H         ; Store result in memory
HLT               ; Halt processor


### Running Programs

1. *Assemble*: Click the "Assemble" button to validate your code
2. *Step*: Execute one instruction at a time to observe data flow
3. *Run*: Execute the entire program automatically
4. *Reset*: Clear all registers and memory to start fresh

### Example Programs

The repository includes 15 example programs demonstrating various operations:
- Basic arithmetic (addition, subtraction)
- Register transfers
- Memory operations
- Flag testing
- Register pair operations

See [EXAMPLES.md](EXAMPLES.md) for complete program listings.

## Architecture


├── app.py                 # Flask backend with Socket.IO
├── templates/
│   └── index.html        # Frontend with SVG-based block diagram
├── examples/             # Sample assembly programs
└── README.md


### Backend (app.py)
- *Processor8085 class*: Simulates registers, flags, memory, and instruction execution
- *Assembler class*: Parses and validates assembly code
- *Socket.IO handlers*: Real-time communication for step-by-step execution

### Frontend (index.html)
- *SVG Block Diagram*: Interactive component visualization
- *Animation Engine*: Data flow particles and wire highlighting
- *Timing Diagram*: Canvas-based machine cycle visualization
- *WebSocket Client*: Real-time updates from backend

## Technical Details

### Control Signals

The simulator accurately represents 8085 control signals:
- *IO/M̅*: Distinguishes memory vs I/O operations
- *S1, S0*: Status signals indicating operation type
- *ALE*: Address Latch Enable for multiplexed bus
- *RD̅, WR̅*: Read and Write control signals

### Machine Cycles

Each instruction is broken down into T-states:
- *T1*: Address on bus (ALE high)
- *T2*: Data transfer (RD̅/WR̅ active)
- *T3*: Decode operation
- *T4+*: Execute with proper control signals

### Data Flow Visualization

The simulator shows:
- Component activation with highlighting
- Wire/bus activation with glowing effects
- Animated particles flowing between components
- Sequential execution with configurable delays

## Educational Use

This simulator is ideal for:
- Computer Science students learning microprocessor architecture
- Assembly language programming courses
- Understanding CPU internals and machine cycles
- Visualizing fetch-decode-execute cycles

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Areas for Improvement
- Add more instructions (logical operations, rotate, etc.)
- Implement interrupts and I/O operations
- Add breakpoint functionality
- Memory editor for direct memory manipulation
- Export/import assembly programs
- Dark mode support

## Roadmap

- [ ] Complete instruction set implementation
- [ ] Interrupt handling
- [ ] I/O port simulation
- [ ] Breakpoint debugging
- [ ] Save/load programs
- [ ] Code syntax highlighting
- [ ] Multiple program examples
- [ ] Mobile responsive design

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Intel 8085 Microprocessor Architecture
- Flask and Socket.IO documentation
- Computer Architecture educators and students

## Contact

Adarsh Singh - [@adarsh-singh-2711782b2](https://www.linkedin.com/in/adarsh-singh-2711782b2/)

Project Link: [https://github.com/AdarshSinghEE/8085-simulator](https://github.com/AdarshSinghEE/digital_8085)

---

⭐ Star this repo if you find it useful!

📧 Feel free to reach out with questions or suggestions!
