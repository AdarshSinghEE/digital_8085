from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import re
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

class Processor8085:
    def __init__(self):
        # Registers
        self.registers = {
            'A': 0x00, 'B': 0x00, 'C': 0x00, 'D': 0x00,
            'E': 0x00, 'H': 0x00, 'L': 0x00
        }
        self.flags = {'S': 0, 'Z': 0, 'AC': 0, 'P': 0, 'CY': 0}
        self.PC = 0x0000  # Program Counter
        self.SP = 0xFFFF  # Stack Pointer
        self.memory = [0x00] * 65536
        self.instruction_set = self._init_instruction_set()
        
    def _init_instruction_set(self):
        return {
            'MOV': {'cycles': 1, 'bytes': 1},
            'MVI': {'cycles': 2, 'bytes': 2},
            'LDA': {'cycles': 4, 'bytes': 3},
            'STA': {'cycles': 4, 'bytes': 3},
            'LHLD': {'cycles': 5, 'bytes': 3},
            'SHLD': {'cycles': 5, 'bytes': 3},
            'LXI': {'cycles': 3, 'bytes': 3},
            'ADD': {'cycles': 1, 'bytes': 1},
            'ADI': {'cycles': 2, 'bytes': 2},
            'SUB': {'cycles': 1, 'bytes': 1},
            'SUI': {'cycles': 2, 'bytes': 2},
            'INR': {'cycles': 1, 'bytes': 1},
            'DCR': {'cycles': 1, 'bytes': 1},
            'INX': {'cycles': 1, 'bytes': 1},
            'DCX': {'cycles': 1, 'bytes': 1},
            'JMP': {'cycles': 3, 'bytes': 3},
            'JZ': {'cycles': 3, 'bytes': 3},
            'JNZ': {'cycles': 3, 'bytes': 3},
            'CALL': {'cycles': 5, 'bytes': 3},
            'RET': {'cycles': 3, 'bytes': 1},
            'PUSH': {'cycles': 3, 'bytes': 1},
            'POP': {'cycles': 3, 'bytes': 1},
            'HLT': {'cycles': 1, 'bytes': 1},
            'NOP': {'cycles': 1, 'bytes': 1},
        }
    
    def reset(self):
        self.registers = {k: 0x00 for k in self.registers}
        self.flags = {k: 0 for k in self.flags}
        self.PC = 0x0000
        self.SP = 0xFFFF
        self.memory = [0x00] * 65536
    
    def get_state(self):
        return {
            'registers': self.registers.copy(),
            'flags': self.flags.copy(),
            'PC': self.PC,
            'SP': self.SP,
            'memory_snippet': {hex(i): self.memory[i] for i in range(min(100, len(self.memory)))}
        }
    
    def update_flags(self, result):
        result &= 0xFF
        self.flags['Z'] = 1 if result == 0 else 0
        self.flags['S'] = 1 if result & 0x80 else 0
        self.flags['P'] = 1 if bin(result).count('1') % 2 == 0 else 0
        return result
    
    def get_register_pair(self, pair):
        if pair == 'B':
            return (self.registers['B'] << 8) | self.registers['C']
        elif pair == 'D':
            return (self.registers['D'] << 8) | self.registers['E']
        elif pair == 'H':
            return (self.registers['H'] << 8) | self.registers['L']
        return 0
    
    def set_register_pair(self, pair, value):
        value &= 0xFFFF
        if pair == 'B':
            self.registers['B'] = (value >> 8) & 0xFF
            self.registers['C'] = value & 0xFF
        elif pair == 'D':
            self.registers['D'] = (value >> 8) & 0xFF
            self.registers['E'] = value & 0xFF
        elif pair == 'H':
            self.registers['H'] = (value >> 8) & 0xFF
            self.registers['L'] = value & 0xFF

class Assembler:
    def __init__(self):
        self.labels = {}
        self.instructions = []
        
    def parse(self, code):
        lines = code.strip().split('\n')
        errors = []
        address = 0x0000
        
        # First pass: collect labels
        for line_num, line in enumerate(lines, 1):
            line = line.split(';')[0].strip()
            if not line:
                continue
                
            if ':' in line:
                label = line.split(':')[0].strip()
                self.labels[label] = address
                line = line.split(':', 1)[1].strip()
                if not line:
                    continue
            
            parts = re.split(r'[,\s]+', line)
            instruction = parts[0].upper()
            
            if instruction in ['MOV', 'ADD', 'SUB', 'INR', 'DCR', 'PUSH', 'POP', 'INX', 'DCX', 'RET', 'HLT', 'NOP']:
                address += 1
            elif instruction in ['MVI', 'ADI', 'SUI']:
                address += 2
            elif instruction in ['LDA', 'STA', 'LHLD', 'SHLD', 'LXI', 'JMP', 'JZ', 'JNZ', 'CALL']:
                address += 3
        
        # Second pass: parse instructions
        address = 0x0000
        for line_num, line in enumerate(lines, 1):
            original_line = line
            line = line.split(';')[0].strip()
            if not line:
                continue
                
            if ':' in line:
                line = line.split(':', 1)[1].strip()
                if not line:
                    continue
            
            parts = re.split(r'[,\s]+', line)
            instruction = parts[0].upper()
            
            if instruction not in ['MOV', 'MVI', 'LDA', 'STA', 'LHLD', 'SHLD', 'LXI', 'ADD', 'ADI', 
                                   'SUB', 'SUI', 'INR', 'DCR', 'INX', 'DCX', 'JMP', 'JZ', 'JNZ', 
                                   'CALL', 'RET', 'PUSH', 'POP', 'HLT', 'NOP']:
                errors.append(f"Line {line_num}: Unknown instruction '{instruction}'")
                continue
            
            try:
                parsed = self._parse_instruction(instruction, parts[1:], address, line_num)
                self.instructions.append(parsed)
                address += parsed['bytes']
            except Exception as e:
                errors.append(f"Line {line_num}: {str(e)}")
        
        return {'success': len(errors) == 0, 'errors': errors, 'instructions': self.instructions}
    
    def _parse_instruction(self, instr, operands, address, line_num):
        result = {'instruction': instr, 'operands': [], 'address': address, 'bytes': 1}
        
        if instr == 'MOV':
            if len(operands) != 2:
                raise ValueError("MOV requires 2 operands")
            result['operands'] = [operands[0].upper(), operands[1].upper()]
            
        elif instr in ['MVI', 'ADI', 'SUI']:
            if len(operands) != 2:
                raise ValueError(f"{instr} requires 2 operands")
            result['operands'] = [operands[0].upper(), self._parse_value(operands[1])]
            result['bytes'] = 2
            
        elif instr in ['LDA', 'STA']:
            if len(operands) != 1:
                raise ValueError(f"{instr} requires 1 operand")
            result['operands'] = [self._parse_address(operands[0])]
            result['bytes'] = 3
            
        elif instr in ['LHLD', 'SHLD']:
            if len(operands) != 1:
                raise ValueError(f"{instr} requires 1 operand")
            result['operands'] = [self._parse_address(operands[0])]
            result['bytes'] = 3
            
        elif instr == 'LXI':
            if len(operands) != 2:
                raise ValueError("LXI requires 2 operands")
            result['operands'] = [operands[0].upper(), self._parse_address(operands[1])]
            result['bytes'] = 3
            
        elif instr in ['ADD', 'SUB', 'INR', 'DCR']:
            if len(operands) != 1:
                raise ValueError(f"{instr} requires 1 operand")
            result['operands'] = [operands[0].upper()]
            
        elif instr in ['INX', 'DCX', 'PUSH', 'POP']:
            if len(operands) != 1:
                raise ValueError(f"{instr} requires 1 operand")
            result['operands'] = [operands[0].upper()]
            
        elif instr in ['JMP', 'JZ', 'JNZ', 'CALL']:
            if len(operands) != 1:
                raise ValueError(f"{instr} requires 1 operand")
            addr = operands[0]
            if addr in self.labels:
                result['operands'] = [self.labels[addr]]
            else:
                result['operands'] = [self._parse_address(addr)]
            result['bytes'] = 3
            
        elif instr in ['RET', 'HLT', 'NOP']:
            result['operands'] = []
            
        return result
    
    def _parse_value(self, val):
        val = val.strip()
        if val.endswith('H'):
            return int(val[:-1], 16)
        elif val.startswith('0X'):
            return int(val, 16)
        else:
            return int(val)
    
    def _parse_address(self, addr):
        addr = addr.strip()
        if addr in self.labels:
            return self.labels[addr]
        if addr.endswith('H'):
            return int(addr[:-1], 16)
        elif addr.startswith('0X'):
            return int(addr, 16)
        else:
            return int(addr)

processor = Processor8085()
assembler = Assembler()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('assemble')
def handle_assemble(data):
    global assembler, processor
    assembler = Assembler()
    processor.reset()
    
    result = assembler.parse(data['code'])
    
    if result['success']:
        # Load instructions into memory
        address = 0x0000
        for instr in result['instructions']:
            processor.memory[address] = instr
            address += instr['bytes']
        
        emit('assemble_result', {'success': True, 'message': 'Assembly successful!'})
    else:
        emit('assemble_result', {'success': False, 'errors': result['errors']})

@socketio.on('execute_step')
def handle_execute_step():
    global processor
    
    if processor.PC >= len(assembler.instructions):
        emit('execution_complete', {'message': 'Program execution complete'})
        return
    
    # Find current instruction
    current_instr = None
    for instr in assembler.instructions:
        if instr['address'] == processor.PC:
            current_instr = instr
            break
    
    if not current_instr:
        emit('execution_error', {'message': 'No instruction at current PC'})
        return
    
    # Execute instruction with animation steps
    animation_steps = execute_instruction(current_instr)
    
    # Send each animation step with proper delay
    for i, step in enumerate(animation_steps):
        socketio.sleep(1.2)  # 1.2 second delay between steps for observation
        emit('animation_step', step)
    
    # Update PC
    if current_instr['instruction'] not in ['JMP', 'JZ', 'JNZ', 'CALL', 'RET', 'HLT']:
        processor.PC += current_instr['bytes']
    
    socketio.sleep(0.3)
    emit('state_update', processor.get_state())

def execute_instruction(instr):
    steps = []
    instruction = instr['instruction']
    operands = instr['operands']
    
    # T1 - Fetch cycle - Address on bus
    steps.append({
        'phase': 'FETCH-T1',
        'description': f'T1: PC → Address Bus (Fetching from {hex(processor.PC)})',
        'flow': ['pc', 'addrbuffer', 'address_bus'],
        'values': {'PC': processor.PC},
        'signals': {'iom': '0', 's1': '1', 's0': '1', 'ale': '1', 'rd': '1', 'wr': '1'}
    })
    
    # T2 - Fetch cycle - Read from memory
    steps.append({
        'phase': 'FETCH-T2',
        'description': f'T2: Reading instruction from memory',
        'flow': ['memory', 'data_bus', 'databuffer', 'ir'],
        'values': {},
        'signals': {'iom': '0', 's1': '1', 's0': '1', 'ale': '0', 'rd': '0', 'wr': '1'}
    })
    
    # T3 - Decode cycle
    steps.append({
        'phase': 'DECODE-T3',
        'description': f'T3: Decoding instruction {instruction}',
        'flow': ['ir', 'decoder', 'controlunit'],
        'values': {'Instruction': instruction},
        'signals': {'iom': '0', 's1': '1', 's0': '1', 'ale': '0', 'rd': '1', 'wr': '1'}
    })
    
    # Execute cycle
    if instruction == 'MOV':
        src, dest = operands[0], operands[1]
        if src == 'M':
            # T4 - Read from memory location pointed by HL
            addr = processor.get_register_pair('H')
            value = processor.memory[addr]
            steps.append({
                'phase': 'EXECUTE-T4',
                'description': f'T4: Reading from memory[{hex(addr)}] via H-L pair',
                'flow': ['regh', 'regl', 'addrbuffer', 'address_bus', 'memory', 'data_bus', 'databuffer', dest.lower()],
                'values': {dest: value},
                'signals': {'iom': '0', 's1': '0', 's0': '1', 'ale': '1', 'rd': '0', 'wr': '1'}
            })
        elif dest == 'M':
            # T4 - Write to memory location pointed by HL
            addr = processor.get_register_pair('H')
            value = processor.registers[src]
            processor.memory[addr] = value
            steps.append({
                'phase': 'EXECUTE-T4',
                'description': f'T4: Writing {hex(value)} to memory[{hex(addr)}] via H-L pair',
                'flow': [src.lower(), 'databuffer', 'data_bus', 'memory'],
                'values': {'M': value},
                'signals': {'iom': '0', 's1': '0', 's0': '1', 'ale': '1', 'rd': '1', 'wr': '0'}
            })
        else:
            # T4 - Register to register transfer
            value = processor.registers[src]
            processor.registers[dest] = value
            steps.append({
                'phase': 'EXECUTE-T4',
                'description': f'T4: Moving {hex(value)} from {src} to {dest} via internal bus',
                'flow': [src.lower(), 'internal_bus', dest.lower()],
                'values': {dest: value},
                'signals': {'iom': '1', 's1': '0', 's0': '0', 'ale': '0', 'rd': '1', 'wr': '1'}
            })
    
    elif instruction == 'MVI':
        reg, value = operands[0], operands[1]
        processor.registers[reg] = value & 0xFF
        # T4 - Fetch immediate data
        steps.append({
            'phase': 'EXECUTE-T4',
            'description': f'T4: Loading immediate value {hex(value)} to {reg}',
            'flow': ['memory', 'data_bus', 'databuffer', reg.lower()],
            'values': {reg: value},
            'signals': {'iom': '0', 's1': '0', 's0': '1', 'ale': '1', 'rd': '0', 'wr': '1'}
        })
    
    elif instruction == 'ADD':
        reg = operands[0]
        value = processor.registers[reg]
        accValue = processor.registers['A']
        
        # T4 - Move register to temp
        steps.append({
            'phase': 'EXECUTE-T4',
            'description': f'T4: Moving {reg} value {hex(value)} to temporary register',
            'flow': [reg.lower(), 'internal_bus', 'tempreg'],
            'values': {'TEMP': value},
            'signals': {'iom': '1', 's1': '0', 's0': '0', 'ale': '0', 'rd': '1', 'wr': '1'}
        })
        
        # T5 - ALU Operation
        result = processor.registers['A'] + value
        carry = 1 if result > 0xFF else 0
        result = processor.update_flags(result)
        processor.flags['CY'] = carry
        processor.registers['A'] = result
        
        steps.append({
            'phase': 'EXECUTE-T5',
            'description': f'T5: ALU adding {hex(accValue)} + {hex(value)} = {hex(result)}',
            'flow': ['accumulator', 'alu', 'tempreg', 'alu', 'accumulator', 'flags'],
            'values': {'A': result, 'Flags': processor.flags},
            'signals': {'iom': '1', 's1': '0', 's0': '0', 'ale': '0', 'rd': '1', 'wr': '1'}
        })
    
    elif instruction == 'SUB':
        reg = operands[0]
        value = processor.registers[reg]
        accValue = processor.registers['A']
        
        # T4 - Move register to temp
        steps.append({
            'phase': 'EXECUTE-T4',
            'description': f'T4: Moving {reg} value {hex(value)} to temporary register',
            'flow': [reg.lower(), 'internal_bus', 'tempreg'],
            'values': {'TEMP': value},
            'signals': {'iom': '1', 's1': '0', 's0': '0', 'ale': '0', 'rd': '1', 'wr': '1'}
        })
        
        # T5 - ALU Operation
        result = processor.registers['A'] - value
        borrow = 1 if result < 0 else 0
        result = processor.update_flags(result & 0xFF)
        processor.flags['CY'] = borrow
        processor.registers['A'] = result
        
        steps.append({
            'phase': 'EXECUTE-T5',
            'description': f'T5: ALU subtracting {hex(accValue)} - {hex(value)} = {hex(result)}',
            'flow': ['accumulator', 'alu', 'tempreg', 'alu', 'accumulator', 'flags'],
            'values': {'A': result, 'Flags': processor.flags},
            'signals': {'iom': '1', 's1': '0', 's0': '0', 'ale': '0', 'rd': '1', 'wr': '1'}
        })
    
    elif instruction == 'INR':
        reg = operands[0]
        oldValue = processor.registers[reg]
        value = processor.registers[reg] + 1
        processor.registers[reg] = processor.update_flags(value)
        
        steps.append({
            'phase': 'EXECUTE-T4',
            'description': f'T4: Incrementing {reg} from {hex(oldValue)} to {hex(processor.registers[reg])}',
            'flow': [reg.lower(), 'alu', reg.lower(), 'flags'],
            'values': {reg: processor.registers[reg]},
            'signals': {'iom': '1', 's1': '0', 's0': '0', 'ale': '0', 'rd': '1', 'wr': '1'}
        })
    
    elif instruction == 'STA':
        address = operands[0]
        value = processor.registers['A']
        processor.memory[address] = value
        
        # T4 - Address low on bus
        steps.append({
            'phase': 'EXECUTE-T4',
            'description': f'T4: Placing address {hex(address)} on address bus',
            'flow': ['databuffer', 'address_bus'],
            'values': {},
            'signals': {'iom': '0', 's1': '0', 's0': '1', 'ale': '1', 'rd': '1', 'wr': '1'}
        })
        
        # T5 - Write data
        steps.append({
            'phase': 'EXECUTE-T5',
            'description': f'T5: Writing accumulator value {hex(value)} to memory[{hex(address)}]',
            'flow': ['accumulator', 'databuffer', 'data_bus', 'memory'],
            'values': {'M': value},
            'signals': {'iom': '0', 's1': '0', 's0': '1', 'ale': '0', 'rd': '1', 'wr': '0'}
        })
    
    elif instruction == 'JMP':
        address = operands[0]
        processor.PC = address
        
        steps.append({
            'phase': 'EXECUTE-T4',
            'description': f'T4: Loading jump address {hex(address)} into PC',
            'flow': ['databuffer', 'pc'],
            'values': {'PC': address},
            'signals': {'iom': '0', 's1': '0', 's0': '1', 'ale': '0', 'rd': '1', 'wr': '1'}
        })
    
    elif instruction == 'HLT':
        steps.append({
            'phase': 'HALT',
            'description': 'HALT: Processor stopped',
            'flow': ['controlunit'],
            'values': {},
            'signals': {'iom': '1', 's1': '0', 's0': '0', 'ale': '0', 'rd': '1', 'wr': '1'}
        })
    
    return steps

@socketio.on('reset')
def handle_reset():
    global processor, assembler
    processor.reset()
    assembler = Assembler()
    emit('state_update', processor.get_state())

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)