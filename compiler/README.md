# Build Your Own Compiler

Create compilers from scratch and understand how high-level languages are translated to machine code. Learn lexical analysis, parsing, semantic analysis, code generation, and optimization.

## 🎯 What You'll Learn

- Lexical analysis and tokenization for compiler frontend
- Parsing techniques and syntax analysis
- Abstract syntax trees and intermediate representations
- Semantic analysis and type checking
- Code generation for target architectures
- Compiler optimizations and performance tuning

## 📋 Prerequisites

- Strong understanding of programming language concepts
- Knowledge of computer architecture and assembly language
- Familiarity with data structures and algorithms
- Basic understanding of formal language theory

## 🏗️ Architecture Overview

Our compiler consists of these core phases:

1. **Lexical Analyzer**: Converts source code to tokens
2. **Parser**: Builds abstract syntax tree from tokens  
3. **Semantic Analyzer**: Type checking and symbol resolution
4. **IR Generator**: Creates intermediate representation
5. **Optimizer**: Improves code efficiency
6. **Code Generator**: Produces target machine code

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│Source Code  │───▶│    Lexer     │───▶│     Tokens      │
│             │    │              │    │                 │
└─────────────┘    └──────────────┘    └─────────────────┘
                                                 │
┌─────────────┐    ┌──────────────┐              ▼
│Machine Code │◄───│ Code Gen     │    ┌─────────────────┐
│   (asm/obj) │    │              │    │     Parser      │
└─────────────┘    └──────────────┘    │                 │
                          ▲             └─────────────────┘
┌─────────────┐           │                       │
│  Optimizer  │───────────┘                       ▼
│             │                         ┌─────────────────┐
└─────────────┘                         │  Semantic       │
                          ┌─────────────│  Analyzer       │
                          │             └─────────────────┘
                          ▼                       │
                ┌─────────────────┐               ▼
                │ Intermediate    │    ┌─────────────────┐
                │ Representation  │◄───│   AST Nodes     │
                │     (IR)        │    │                 │
                └─────────────────┘    └─────────────────┘
```

## 🚀 Implementation Steps

### Step 1: Target Architecture Definition

Define the target machine architecture and instruction set.

```python
from enum import Enum, auto
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

class RegisterType(Enum):
    GENERAL = "general"
    SPECIAL = "special"
    STACK = "stack"

class InstructionType(Enum):
    # Arithmetic
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    
    # Logical
    AND = "and"
    OR = "or"
    NOT = "not"
    XOR = "xor"
    
    # Comparison
    CMP = "cmp"
    
    # Control flow
    JMP = "jmp"      # Unconditional jump
    JEQ = "jeq"      # Jump if equal
    JNE = "jne"      # Jump if not equal
    JLT = "jlt"      # Jump if less than
    JLE = "jle"      # Jump if less than or equal
    JGT = "jgt"      # Jump if greater than
    JGE = "jge"      # Jump if greater than or equal
    
    # Memory
    LOAD = "load"    # Load from memory
    STORE = "store"  # Store to memory
    MOVE = "move"    # Move between registers
    
    # Stack
    PUSH = "push"
    POP = "pop"
    
    # Function calls
    CALL = "call"
    RET = "ret"
    
    # Special
    HALT = "halt"
    NOP = "nop"

@dataclass
class Register:
    name: str
    type: RegisterType
    size: int  # bits

class TargetMachine:
    """Virtual target machine specification"""
    def __init__(self):
        # General-purpose registers
        self.registers = {
            'R0': Register('R0', RegisterType.GENERAL, 32),
            'R1': Register('R1', RegisterType.GENERAL, 32),
            'R2': Register('R2', RegisterType.GENERAL, 32),
            'R3': Register('R3', RegisterType.GENERAL, 32),
            'R4': Register('R4', RegisterType.GENERAL, 32),
            'R5': Register('R5', RegisterType.GENERAL, 32),
            'R6': Register('R6', RegisterType.GENERAL, 32),
            'R7': Register('R7', RegisterType.GENERAL, 32),
        }
        
        # Special registers
        self.registers.update({
            'SP': Register('SP', RegisterType.STACK, 32),    # Stack pointer
            'BP': Register('BP', RegisterType.STACK, 32),    # Base pointer
            'PC': Register('PC', RegisterType.SPECIAL, 32),  # Program counter
            'FLAGS': Register('FLAGS', RegisterType.SPECIAL, 32),  # Flags register
        })
        
        # Memory layout
        self.memory_size = 1024 * 1024  # 1MB
        self.word_size = 4  # 32-bit words
        
        # Instruction encoding
        self.instruction_size = 4  # bytes

@dataclass
class Operand:
    """Instruction operand"""
    pass

@dataclass  
class RegisterOperand(Operand):
    register: str

@dataclass
class ImmediateOperand(Operand):
    value: int

@dataclass
class MemoryOperand(Operand):
    address: Union[int, str]  # Absolute address or label

@dataclass
class Instruction:
    """Machine instruction"""
    opcode: InstructionType
    operands: List[Operand]
    label: Optional[str] = None
    
    def __str__(self) -> str:
        operand_str = ", ".join(str(op) for op in self.operands)
        return f"{self.opcode.value} {operand_str}"
```

### Step 2: Intermediate Representation

Create an intermediate representation for compiler optimizations.

```python
from typing import Any, Set
from dataclasses import dataclass
from abc import ABC, abstractmethod

class IRValue(ABC):
    """Base class for IR values"""
    pass

@dataclass
class IRConstant(IRValue):
    value: Any
    type: str
    
    def __str__(self):
        return f"{self.value}"

@dataclass  
class IRVariable(IRValue):
    name: str
    type: str
    
    def __str__(self):
        return f"%{self.name}"

@dataclass
class IRTemporary(IRValue):
    id: int
    type: str
    
    def __str__(self):
        return f"%t{self.id}"

class IRInstruction(ABC):
    """Base class for IR instructions"""
    def __init__(self, result: Optional[IRValue] = None):
        self.result = result
    
    @abstractmethod
    def get_uses(self) -> Set[IRValue]:
        """Get variables/temporaries used by this instruction"""
        pass
    
    @abstractmethod
    def get_def(self) -> Optional[IRValue]:
        """Get variable/temporary defined by this instruction"""
        pass

@dataclass
class IRBinaryOp(IRInstruction):
    operator: str
    left: IRValue
    right: IRValue
    result: IRValue
    
    def get_uses(self) -> Set[IRValue]:
        return {self.left, self.right}
    
    def get_def(self) -> Optional[IRValue]:
        return self.result
    
    def __str__(self):
        return f"{self.result} = {self.left} {self.operator} {self.right}"

@dataclass
class IRUnaryOp(IRInstruction):
    operator: str
    operand: IRValue
    result: IRValue
    
    def get_uses(self) -> Set[IRValue]:
        return {self.operand}
    
    def get_def(self) -> Optional[IRValue]:
        return self.result
    
    def __str__(self):
        return f"{self.result} = {self.operator} {self.operand}"

@dataclass
class IRAssignment(IRInstruction):
    target: IRValue
    source: IRValue
    
    def get_uses(self) -> Set[IRValue]:
        return {self.source}
    
    def get_def(self) -> Optional[IRValue]:
        return self.target
    
    def __str__(self):
        return f"{self.target} = {self.source}"

@dataclass
class IRLabel(IRInstruction):
    name: str
    
    def get_uses(self) -> Set[IRValue]:
        return set()
    
    def get_def(self) -> Optional[IRValue]:
        return None
    
    def __str__(self):
        return f"{self.name}:"

@dataclass
class IRJump(IRInstruction):
    target: str
    
    def get_uses(self) -> Set[IRValue]:
        return set()
    
    def get_def(self) -> Optional[IRValue]:
        return None
    
    def __str__(self):
        return f"jump {self.target}"

@dataclass  
class IRConditionalJump(IRInstruction):
    condition: IRValue
    true_target: str
    false_target: str
    
    def get_uses(self) -> Set[IRValue]:
        return {self.condition}
    
    def get_def(self) -> Optional[IRValue]:
        return None
    
    def __str__(self):
        return f"if {self.condition} jump {self.true_target} else {self.false_target}"

@dataclass
class IRFunctionCall(IRInstruction):
    function: str
    arguments: List[IRValue]
    result: Optional[IRValue]
    
    def get_uses(self) -> Set[IRValue]:
        return set(self.arguments)
    
    def get_def(self) -> Optional[IRValue]:
        return self.result
    
    def __str__(self):
        args_str = ", ".join(str(arg) for arg in self.arguments)
        if self.result:
            return f"{self.result} = call {self.function}({args_str})"
        else:
            return f"call {self.function}({args_str})"

@dataclass
class IRReturn(IRInstruction):
    value: Optional[IRValue] = None
    
    def get_uses(self) -> Set[IRValue]:
        return {self.value} if self.value else set()
    
    def get_def(self) -> Optional[IRValue]:
        return None
    
    def __str__(self):
        if self.value:
            return f"return {self.value}"
        else:
            return "return"

class IRBasicBlock:
    """Basic block in control flow graph"""
    def __init__(self, name: str):
        self.name = name
        self.instructions: List[IRInstruction] = []
        self.predecessors: Set['IRBasicBlock'] = set()
        self.successors: Set['IRBasicBlock'] = set()
    
    def add_instruction(self, instr: IRInstruction):
        self.instructions.append(instr)
    
    def __str__(self):
        lines = [f"{self.name}:"]
        for instr in self.instructions:
            lines.append(f"    {instr}")
        return "\n".join(lines)

class IRFunction:
    """IR function representation"""
    def __init__(self, name: str, parameters: List[IRVariable]):
        self.name = name
        self.parameters = parameters
        self.basic_blocks: List[IRBasicBlock] = []
        self.entry_block: Optional[IRBasicBlock] = None
        self.temp_counter = 0
    
    def create_temp(self, type_name: str = "int") -> IRTemporary:
        temp = IRTemporary(self.temp_counter, type_name)
        self.temp_counter += 1
        return temp
    
    def add_basic_block(self, name: str) -> IRBasicBlock:
        block = IRBasicBlock(name)
        self.basic_blocks.append(block)
        if self.entry_block is None:
            self.entry_block = block
        return block
    
    def __str__(self):
        param_str = ", ".join(str(p) for p in self.parameters)
        lines = [f"function {self.name}({param_str}) {{"]
        
        for block in self.basic_blocks:
            lines.append(str(block))
            lines.append("")
        
        lines.append("}")
        return "\n".join(lines)
```

### Step 3: AST to IR Translation

Convert AST nodes to intermediate representation.

```python
from typing import Dict, List, Optional, Union

class IRGenerator:
    """Generates IR from AST"""
    
    def __init__(self):
        self.current_function: Optional[IRFunction] = None
        self.current_block: Optional[IRBasicBlock] = None
        self.symbol_table: Dict[str, IRVariable] = {}
        self.label_counter = 0
        self.functions: List[IRFunction] = []
    
    def create_label(self) -> str:
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label
    
    def generate_program(self, program: 'Program') -> List[IRFunction]:
        """Generate IR for entire program"""
        for stmt in program.statements:
            if isinstance(stmt, FunctionDeclaration):
                self.generate_function(stmt)
        return self.functions
    
    def generate_function(self, func_decl: 'FunctionDeclaration'):
        """Generate IR for function declaration"""
        # Create IR parameters
        ir_params = []
        for param in func_decl.parameters:
            ir_param = IRVariable(param.value, "int")  # Assume int type for now
            ir_params.append(ir_param)
            self.symbol_table[param.value] = ir_param
        
        # Create IR function
        ir_func = IRFunction(func_decl.name.value, ir_params)
        self.current_function = ir_func
        
        # Create entry block
        entry_block = ir_func.add_basic_block("entry")
        self.current_block = entry_block
        
        # Generate function body
        for stmt in func_decl.body:
            self.generate_statement(stmt)
        
        # Add implicit return if needed
        if (not self.current_block.instructions or 
            not isinstance(self.current_block.instructions[-1], IRReturn)):
            self.current_block.add_instruction(IRReturn())
        
        self.functions.append(ir_func)
        self.current_function = None
        self.current_block = None
    
    def generate_statement(self, stmt: 'Statement') -> Optional[IRValue]:
        """Generate IR for statement"""
        if isinstance(stmt, Assignment):
            return self.generate_assignment(stmt)
        elif isinstance(stmt, ExpressionStatement):
            return self.generate_expression(stmt.expression)
        elif isinstance(stmt, IfStatement):
            return self.generate_if_statement(stmt)
        elif isinstance(stmt, WhileStatement):
            return self.generate_while_statement(stmt)
        elif isinstance(stmt, ReturnStatement):
            return self.generate_return_statement(stmt)
        elif isinstance(stmt, Block):
            return self.generate_block(stmt)
        else:
            raise NotImplementedError(f"Statement type {type(stmt)} not implemented")
    
    def generate_expression(self, expr: 'Expression') -> IRValue:
        """Generate IR for expression"""
        if isinstance(expr, Literal):
            return IRConstant(expr.value, self.infer_type(expr.value))
        elif isinstance(expr, Identifier):
            if expr.name in self.symbol_table:
                return self.symbol_table[expr.name]
            else:
                raise NameError(f"Undefined variable: {expr.name}")
        elif isinstance(expr, BinaryOp):
            return self.generate_binary_op(expr)
        elif isinstance(expr, UnaryOp):
            return self.generate_unary_op(expr)
        elif isinstance(expr, FunctionCall):
            return self.generate_function_call(expr)
        else:
            raise NotImplementedError(f"Expression type {type(expr)} not implemented")
    
    def generate_assignment(self, assignment: 'Assignment') -> IRValue:
        """Generate IR for assignment"""
        value = self.generate_expression(assignment.value)
        
        # Get or create variable
        var_name = assignment.name.value
        if var_name not in self.symbol_table:
            self.symbol_table[var_name] = IRVariable(var_name, "int")
        
        target = self.symbol_table[var_name]
        
        # Generate assignment instruction
        assign_instr = IRAssignment(target, value)
        self.current_block.add_instruction(assign_instr)
        
        return target
    
    def generate_binary_op(self, binary_op: 'BinaryOp') -> IRValue:
        """Generate IR for binary operation"""
        left = self.generate_expression(binary_op.left)
        right = self.generate_expression(binary_op.right)
        
        # Create temporary for result
        result = self.current_function.create_temp("int")
        
        # Map operator tokens to IR operators
        op_map = {
            TokenType.PLUS: '+',
            TokenType.MINUS: '-',
            TokenType.MULTIPLY: '*',
            TokenType.DIVIDE: '/',
            TokenType.MODULO: '%',
            TokenType.EQUAL: '==',
            TokenType.NOT_EQUAL: '!=',
            TokenType.LESS: '<',
            TokenType.LESS_EQUAL: '<=',
            TokenType.GREATER: '>',
            TokenType.GREATER_EQUAL: '>=',
            TokenType.AND: '&&',
            TokenType.OR: '||',
        }
        
        ir_op = op_map.get(binary_op.operator.type)
        if ir_op is None:
            raise NotImplementedError(f"Binary operator {binary_op.operator.value} not implemented")
        
        # Generate binary operation instruction
        bin_op = IRBinaryOp(ir_op, left, right, result)
        self.current_block.add_instruction(bin_op)
        
        return result
    
    def generate_unary_op(self, unary_op: 'UnaryOp') -> IRValue:
        """Generate IR for unary operation"""
        operand = self.generate_expression(unary_op.operand)
        result = self.current_function.create_temp("int")
        
        op_map = {
            TokenType.MINUS: '-',
            TokenType.NOT: '!',
        }
        
        ir_op = op_map.get(unary_op.operator.type)
        if ir_op is None:
            raise NotImplementedError(f"Unary operator {unary_op.operator.value} not implemented")
        
        unary_instr = IRUnaryOp(ir_op, operand, result)
        self.current_block.add_instruction(unary_instr)
        
        return result
    
    def generate_if_statement(self, if_stmt: 'IfStatement') -> None:
        """Generate IR for if statement"""
        condition = self.generate_expression(if_stmt.condition)
        
        # Create labels for control flow
        then_label = self.create_label()
        else_label = self.create_label() if if_stmt.else_branch else None
        end_label = self.create_label()
        
        # Generate conditional jump
        if else_label:
            cond_jump = IRConditionalJump(condition, then_label, else_label)
        else:
            cond_jump = IRConditionalJump(condition, then_label, end_label)
        self.current_block.add_instruction(cond_jump)
        
        # Generate then block
        then_block = self.current_function.add_basic_block(then_label)
        self.current_block = then_block
        self.current_block.add_instruction(IRLabel(then_label))
        
        self.generate_statement(if_stmt.then_branch)
        
        # Jump to end (unless block ends with return)
        if (not self.current_block.instructions or 
            not isinstance(self.current_block.instructions[-1], IRReturn)):
            self.current_block.add_instruction(IRJump(end_label))
        
        # Generate else block if present
        if if_stmt.else_branch:
            else_block = self.current_function.add_basic_block(else_label)
            self.current_block = else_block
            self.current_block.add_instruction(IRLabel(else_label))
            
            self.generate_statement(if_stmt.else_branch)
            
            # Jump to end
            if (not self.current_block.instructions or 
                not isinstance(self.current_block.instructions[-1], IRReturn)):
                self.current_block.add_instruction(IRJump(end_label))
        
        # Create end block
        end_block = self.current_function.add_basic_block(end_label)
        self.current_block = end_block
        self.current_block.add_instruction(IRLabel(end_label))
    
    def generate_while_statement(self, while_stmt: 'WhileStatement') -> None:
        """Generate IR for while statement"""
        loop_label = self.create_label()
        body_label = self.create_label()
        end_label = self.create_label()
        
        # Jump to loop condition
        self.current_block.add_instruction(IRJump(loop_label))
        
        # Generate loop condition block
        loop_block = self.current_function.add_basic_block(loop_label)
        self.current_block = loop_block
        self.current_block.add_instruction(IRLabel(loop_label))
        
        condition = self.generate_expression(while_stmt.condition)
        cond_jump = IRConditionalJump(condition, body_label, end_label)
        self.current_block.add_instruction(cond_jump)
        
        # Generate body block
        body_block = self.current_function.add_basic_block(body_label)
        self.current_block = body_block
        self.current_block.add_instruction(IRLabel(body_label))
        
        self.generate_statement(while_stmt.body)
        
        # Jump back to condition
        self.current_block.add_instruction(IRJump(loop_label))
        
        # Create end block
        end_block = self.current_function.add_basic_block(end_label)
        self.current_block = end_block
        self.current_block.add_instruction(IRLabel(end_label))
    
    def generate_function_call(self, func_call: 'FunctionCall') -> IRValue:
        """Generate IR for function call"""
        # Generate arguments
        args = []
        for arg_expr in func_call.arguments:
            args.append(self.generate_expression(arg_expr))
        
        # Get function name
        if isinstance(func_call.callee, Identifier):
            func_name = func_call.callee.name
        else:
            raise NotImplementedError("Function expressions not supported")
        
        # Create temporary for result
        result = self.current_function.create_temp("int")
        
        # Generate call instruction
        call_instr = IRFunctionCall(func_name, args, result)
        self.current_block.add_instruction(call_instr)
        
        return result
    
    def generate_return_statement(self, return_stmt: 'ReturnStatement') -> None:
        """Generate IR for return statement"""
        value = None
        if return_stmt.value:
            value = self.generate_expression(return_stmt.value)
        
        return_instr = IRReturn(value)
        self.current_block.add_instruction(return_instr)
    
    def generate_block(self, block: 'Block') -> None:
        """Generate IR for block statement"""
        for stmt in block.statements:
            self.generate_statement(stmt)
    
    def infer_type(self, value: Any) -> str:
        """Infer type from Python value"""
        if isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, bool):
            return "bool"
        elif isinstance(value, str):
            return "string"
        else:
            return "unknown"
```

### Step 4: Register Allocation

Implement register allocation for efficient code generation.

```python
from typing import Dict, Set, List, Optional
from collections import defaultdict
import itertools

class LivenessAnalyzer:
    """Performs liveness analysis for register allocation"""
    
    def __init__(self, function: IRFunction):
        self.function = function
        self.live_in: Dict[IRBasicBlock, Set[IRValue]] = defaultdict(set)
        self.live_out: Dict[IRBasicBlock, Set[IRValue]] = defaultdict(set)
    
    def analyze(self):
        """Perform liveness analysis using iterative data flow"""
        changed = True
        
        while changed:
            changed = False
            
            for block in reversed(self.function.basic_blocks):
                old_live_in = self.live_in[block].copy()
                old_live_out = self.live_out[block].copy()
                
                # live_out[B] = Union of live_in[S] for all successors S
                self.live_out[block].clear()
                for successor in block.successors:
                    self.live_out[block].update(self.live_in[successor])
                
                # live_in[B] = use[B] U (live_out[B] - def[B])
                use_set, def_set = self.get_use_def_sets(block)
                self.live_in[block] = use_set | (self.live_out[block] - def_set)
                
                if (old_live_in != self.live_in[block] or 
                    old_live_out != self.live_out[block]):
                    changed = True
    
    def get_use_def_sets(self, block: IRBasicBlock) -> tuple[Set[IRValue], Set[IRValue]]:
        """Get use and def sets for a basic block"""
        use_set = set()
        def_set = set()
        
        for instr in block.instructions:
            # Add uses (variables read before being defined in this block)
            for var in instr.get_uses():
                if var not in def_set:
                    use_set.add(var)
            
            # Add definitions
            defined_var = instr.get_def()
            if defined_var:
                def_set.add(defined_var)
        
        return use_set, def_set

class InterferenceGraph:
    """Interference graph for register allocation"""
    
    def __init__(self):
        self.nodes: Set[IRValue] = set()
        self.edges: Set[tuple[IRValue, IRValue]] = set()
        self.adjacency: Dict[IRValue, Set[IRValue]] = defaultdict(set)
    
    def add_node(self, node: IRValue):
        self.nodes.add(node)
    
    def add_edge(self, node1: IRValue, node2: IRValue):
        if node1 != node2:
            self.edges.add((node1, node2))
            self.edges.add((node2, node1))
            self.adjacency[node1].add(node2)
            self.adjacency[node2].add(node1)
    
    def get_neighbors(self, node: IRValue) -> Set[IRValue]:
        return self.adjacency[node]
    
    def remove_node(self, node: IRValue):
        """Remove node and all its edges"""
        self.nodes.discard(node)
        neighbors = self.adjacency[node].copy()
        
        for neighbor in neighbors:
            self.adjacency[neighbor].discard(node)
            self.edges.discard((node, neighbor))
            self.edges.discard((neighbor, node))
        
        del self.adjacency[node]

class RegisterAllocator:
    """Graph coloring register allocator"""
    
    def __init__(self, target_machine: TargetMachine):
        self.target_machine = target_machine
        self.available_registers = [name for name, reg in target_machine.registers.items() 
                                  if reg.type == RegisterType.GENERAL]
        self.num_colors = len(self.available_registers)
    
    def allocate(self, function: IRFunction) -> Dict[IRValue, str]:
        """Allocate registers using graph coloring"""
        # Build interference graph
        interference_graph = self.build_interference_graph(function)
        
        # Color the graph
        coloring = self.color_graph(interference_graph)
        
        # Map colors to actual registers
        allocation = {}
        for var, color in coloring.items():
            if color < len(self.available_registers):
                allocation[var] = self.available_registers[color]
            else:
                # Spill to memory (simplified - would need stack allocation)
                allocation[var] = f"SPILL_{color - len(self.available_registers)}"
        
        return allocation
    
    def build_interference_graph(self, function: IRFunction) -> InterferenceGraph:
        """Build interference graph from liveness information"""
        # Perform liveness analysis
        liveness = LivenessAnalyzer(function)
        liveness.analyze()
        
        graph = InterferenceGraph()
        
        # Add all variables as nodes
        for block in function.basic_blocks:
            for instr in block.instructions:
                for var in instr.get_uses():
                    if isinstance(var, (IRVariable, IRTemporary)):
                        graph.add_node(var)
                
                defined_var = instr.get_def()
                if defined_var and isinstance(defined_var, (IRVariable, IRTemporary)):
                    graph.add_node(defined_var)
        
        # Add interference edges
        for block in function.basic_blocks:
            live_vars = liveness.live_out[block].copy()
            
            for instr in reversed(block.instructions):
                # Variables that are defined interfere with all live variables
                defined_var = instr.get_def()
                if defined_var and isinstance(defined_var, (IRVariable, IRTemporary)):
                    for live_var in live_vars:
                        if isinstance(live_var, (IRVariable, IRTemporary)):
                            graph.add_edge(defined_var, live_var)
                
                # Remove defined variable from live set
                if defined_var:
                    live_vars.discard(defined_var)
                
                # Add used variables to live set
                for used_var in instr.get_uses():
                    if isinstance(used_var, (IRVariable, IRTemporary)):
                        live_vars.add(used_var)
        
        return graph
    
    def color_graph(self, graph: InterferenceGraph) -> Dict[IRValue, int]:
        """Color interference graph using graph coloring algorithm"""
        coloring = {}
        stack = []
        
        # Make a copy of the graph
        work_graph = InterferenceGraph()
        work_graph.nodes = graph.nodes.copy()
        work_graph.edges = graph.edges.copy()
        work_graph.adjacency = {node: neighbors.copy() 
                               for node, neighbors in graph.adjacency.items()}
        
        # Iteratively remove nodes with degree < k
        while work_graph.nodes:
            # Find node with smallest degree
            min_node = min(work_graph.nodes, 
                          key=lambda n: len(work_graph.get_neighbors(n)))
            
            stack.append((min_node, work_graph.get_neighbors(min_node).copy()))
            work_graph.remove_node(min_node)
        
        # Color nodes in reverse order
        while stack:
            node, neighbors = stack.pop()
            
            # Find available color
            used_colors = set()
            for neighbor in neighbors:
                if neighbor in coloring:
                    used_colors.add(coloring[neighbor])
            
            # Assign first available color
            color = 0
            while color in used_colors:
                color += 1
            
            coloring[node] = color
        
        return coloring
```

### Step 5: Code Generation

Generate target machine code from IR.

```python
class CodeGenerator:
    """Generates target machine code from IR"""
    
    def __init__(self, target_machine: TargetMachine):
        self.target_machine = target_machine
        self.current_function: Optional[IRFunction] = None
        self.register_allocation: Dict[IRValue, str] = {}
        self.instructions: List[Instruction] = []
        self.label_addresses: Dict[str, int] = {}
    
    def generate(self, functions: List[IRFunction]) -> List[Instruction]:
        """Generate machine code for all functions"""
        self.instructions = []
        
        for function in functions:
            self.generate_function(function)
        
        return self.instructions
    
    def generate_function(self, function: IRFunction):
        """Generate machine code for a function"""
        self.current_function = function
        
        # Perform register allocation
        allocator = RegisterAllocator(self.target_machine)
        self.register_allocation = allocator.allocate(function)
        
        # Generate function prologue
        self.generate_function_prologue(function)
        
        # Generate code for each basic block
        for block in function.basic_blocks:
            self.generate_basic_block(block)
        
        # Generate function epilogue
        self.generate_function_epilogue(function)
    
    def generate_function_prologue(self, function: IRFunction):
        """Generate function entry code"""
        # Function label
        func_label = Instruction(InstructionType.NOP, [], function.name)
        self.instructions.append(func_label)
        
        # Save frame pointer and set up stack frame
        self.instructions.append(Instruction(
            InstructionType.PUSH,
            [RegisterOperand('BP')]
        ))
        
        self.instructions.append(Instruction(
            InstructionType.MOVE,
            [RegisterOperand('BP'), RegisterOperand('SP')]
        ))
        
        # Reserve space for local variables (simplified)
        local_vars = len([var for var in self.register_allocation.keys() 
                         if isinstance(var, IRVariable)])
        if local_vars > 0:
            self.instructions.append(Instruction(
                InstructionType.SUB,
                [RegisterOperand('SP'), ImmediateOperand(local_vars * 4)]
            ))
    
    def generate_function_epilogue(self, function: IRFunction):
        """Generate function exit code"""
        # Restore stack pointer
        self.instructions.append(Instruction(
            InstructionType.MOVE,
            [RegisterOperand('SP'), RegisterOperand('BP')]
        ))
        
        # Restore frame pointer
        self.instructions.append(Instruction(
            InstructionType.POP,
            [RegisterOperand('BP')]
        ))
        
        # Return
        self.instructions.append(Instruction(
            InstructionType.RET, []
        ))
    
    def generate_basic_block(self, block: IRBasicBlock):
        """Generate code for a basic block"""
        for instr in block.instructions:
            self.generate_instruction(instr)
    
    def generate_instruction(self, instr: IRInstruction):
        """Generate machine code for IR instruction"""
        if isinstance(instr, IRBinaryOp):
            self.generate_binary_op(instr)
        elif isinstance(instr, IRUnaryOp):
            self.generate_unary_op(instr)
        elif isinstance(instr, IRAssignment):
            self.generate_assignment(instr)
        elif isinstance(instr, IRLabel):
            self.generate_label(instr)
        elif isinstance(instr, IRJump):
            self.generate_jump(instr)
        elif isinstance(instr, IRConditionalJump):
            self.generate_conditional_jump(instr)
        elif isinstance(instr, IRFunctionCall):
            self.generate_function_call(instr)
        elif isinstance(instr, IRReturn):
            self.generate_return(instr)
        else:
            raise NotImplementedError(f"IR instruction {type(instr)} not implemented")
    
    def generate_binary_op(self, instr: IRBinaryOp):
        """Generate code for binary operation"""
        left_reg = self.get_register_for_value(instr.left)
        right_reg = self.get_register_for_value(instr.right)
        result_reg = self.get_register_for_value(instr.result)
        
        # Load operands if they're not in registers
        if left_reg != result_reg:
            self.instructions.append(Instruction(
                InstructionType.MOVE,
                [RegisterOperand(result_reg), self.get_operand_for_value(instr.left)]
            ))
        
        # Generate operation
        op_map = {
            '+': InstructionType.ADD,
            '-': InstructionType.SUB,
            '*': InstructionType.MUL,
            '/': InstructionType.DIV,
            '%': InstructionType.MOD,
        }
        
        machine_op = op_map.get(instr.operator)
        if machine_op:
            self.instructions.append(Instruction(
                machine_op,
                [RegisterOperand(result_reg), self.get_operand_for_value(instr.right)]
            ))
        elif instr.operator in ['==', '!=', '<', '<=', '>', '>=']:
            # Comparison operations
            self.instructions.append(Instruction(
                InstructionType.CMP,
                [self.get_operand_for_value(instr.left), 
                 self.get_operand_for_value(instr.right)]
            ))
            # Set result based on comparison (simplified)
        else:
            raise NotImplementedError(f"Binary operator {instr.operator} not implemented")
    
    def generate_assignment(self, instr: IRAssignment):
        """Generate code for assignment"""
        target_reg = self.get_register_for_value(instr.target)
        source_operand = self.get_operand_for_value(instr.source)
        
        self.instructions.append(Instruction(
            InstructionType.MOVE,
            [RegisterOperand(target_reg), source_operand]
        ))
    
    def generate_label(self, instr: IRLabel):
        """Generate label"""
        self.instructions.append(Instruction(
            InstructionType.NOP, [], instr.name
        ))
    
    def generate_jump(self, instr: IRJump):
        """Generate unconditional jump"""
        self.instructions.append(Instruction(
            InstructionType.JMP,
            [MemoryOperand(instr.target)]
        ))
    
    def generate_conditional_jump(self, instr: IRConditionalJump):
        """Generate conditional jump"""
        # Test condition
        condition_operand = self.get_operand_for_value(instr.condition)
        self.instructions.append(Instruction(
            InstructionType.CMP,
            [condition_operand, ImmediateOperand(0)]
        ))
        
        # Jump if not equal (true)
        self.instructions.append(Instruction(
            InstructionType.JNE,
            [MemoryOperand(instr.true_target)]
        ))
        
        # Jump to false target
        self.instructions.append(Instruction(
            InstructionType.JMP,
            [MemoryOperand(instr.false_target)]
        ))
    
    def generate_function_call(self, instr: IRFunctionCall):
        """Generate function call"""
        # Push arguments (in reverse order for stack)
        for arg in reversed(instr.arguments):
            arg_operand = self.get_operand_for_value(arg)
            self.instructions.append(Instruction(
                InstructionType.PUSH,
                [arg_operand]
            ))
        
        # Call function
        self.instructions.append(Instruction(
            InstructionType.CALL,
            [MemoryOperand(instr.function)]
        ))
        
        # Clean up stack (pop arguments)
        if instr.arguments:
            self.instructions.append(Instruction(
                InstructionType.ADD,
                [RegisterOperand('SP'), 
                 ImmediateOperand(len(instr.arguments) * 4)]
            ))
        
        # Move result to allocated register
        if instr.result:
            result_reg = self.get_register_for_value(instr.result)
            self.instructions.append(Instruction(
                InstructionType.MOVE,
                [RegisterOperand(result_reg), RegisterOperand('R0')]  # Assume R0 holds return value
            ))
    
    def generate_return(self, instr: IRReturn):
        """Generate return statement"""
        if instr.value:
            # Move return value to return register
            value_operand = self.get_operand_for_value(instr.value)
            self.instructions.append(Instruction(
                InstructionType.MOVE,
                [RegisterOperand('R0'), value_operand]
            ))
    
    def get_register_for_value(self, value: IRValue) -> str:
        """Get allocated register for IR value"""
        if value in self.register_allocation:
            return self.register_allocation[value]
        else:
            # Return a default register (simplified)
            return 'R0'
    
    def get_operand_for_value(self, value: IRValue) -> Operand:
        """Get machine operand for IR value"""
        if isinstance(value, IRConstant):
            return ImmediateOperand(value.value)
        else:
            reg = self.get_register_for_value(value)
            if reg.startswith('SPILL_'):
                # Handle spilled variables (simplified - would use stack offsets)
                return MemoryOperand(0)  # Placeholder
            else:
                return RegisterOperand(reg)

# Complete compiler pipeline
class Compiler:
    """Complete compiler implementation"""
    
    def __init__(self, target_machine: TargetMachine):
        self.target_machine = target_machine
    
    def compile(self, source_code: str) -> List[Instruction]:
        """Compile source code to machine instructions"""
        try:
            # Frontend: Lexical analysis
            lexer = Lexer(source_code)
            tokens = lexer.tokenize()
            
            # Frontend: Parsing
            parser = Parser(tokens)
            ast = parser.parse()
            
            # Middle-end: IR generation
            ir_generator = IRGenerator()
            ir_functions = ir_generator.generate_program(ast)
            
            # Backend: Code generation
            code_generator = CodeGenerator(self.target_machine)
            machine_code = code_generator.generate(ir_functions)
            
            return machine_code
            
        except Exception as e:
            print(f"Compilation error: {e}")
            return []
    
    def compile_and_emit_assembly(self, source_code: str) -> str:
        """Compile and emit human-readable assembly"""
        instructions = self.compile(source_code)
        
        assembly_lines = []
        for instr in instructions:
            if instr.label:
                assembly_lines.append(f"{instr.label}:")
            
            operand_str = ", ".join(str(op) for op in instr.operands)
            if operand_str:
                assembly_lines.append(f"    {instr.opcode.value} {operand_str}")
            else:
                assembly_lines.append(f"    {instr.opcode.value}")
        
        return "\n".join(assembly_lines)

# Example usage
if __name__ == "__main__":
    target = TargetMachine()
    compiler = Compiler(target)
    
    test_code = """
    function factorial(n) {
        if (n <= 1) {
            return 1
        } else {
            return n * factorial(n - 1)
        }
    }
    
    function main() {
        let result = factorial(5)
        return result
    }
    """
    
    assembly = compiler.compile_and_emit_assembly(test_code)
    print("Generated Assembly:")
    print(assembly)
```

## 📚 Tutorials by Language

### C
- **[Let's Build a Compiler](https://compilers.iecc.com/crenshaw/)** - Jack Crenshaw's classic tutorial
- **[Compiler Construction](http://www.ethoberon.ethz.ch/WirthPubl/CBEAll.pdf)** - Niklaus Wirth's approach
- **[Writing a C Compiler](https://norasandler.com/2017/11/29/Write-a-Compiler.html)** - Modern C compiler series

### C++
- **[LLVM Tutorial](https://llvm.org/docs/tutorial/MyFirstLanguageFrontend/index.html)** - Building with LLVM
- **[Modern Compiler Implementation in C++](https://www.cs.princeton.edu/~appel/modern/cplusplus/)** - Academic approach
- **[Dragon Book Examples](https://github.com/fool2fish/dragon-book-exercise-answers)** - Classic compiler textbook

### Python
- **[Simple Compiler in Python](https://github.com/rspivak/lsbasi)** - Ruslan's compiler series
- **[Python AST Tutorial](https://greentreesnakes.readthedocs.io/)** - Understanding Python's AST
- **[Building a Compiler with Python](https://blog.usejournal.com/writing-your-own-programming-language-and-compiler-with-python-a468970ae6df)** - Complete implementation

### Go
- **[Writing a Compiler in Go](https://compilerbook.com/)** - Thorsten Ball's compiler book
- **[Go Compiler Internals](https://github.com/golang/go/tree/master/src/cmd/compile)** - Official Go compiler
- **[Simple Go Compiler](https://medium.com/@zappier/building-a-simple-compiler-in-go-6fbf9e8bc8e6)** - Tutorial implementation

### Rust
- **[Rust Compiler Development Guide](https://rustc-dev-guide.rust-lang.org/)** - Official Rust compiler guide
- **[Building a Rust Compiler](https://github.com/rust-lang/rustc_codegen_cranelift)** - Alternative codegen backend
- **[Cranelift Tutorial](https://cranelift.readthedocs.io/en/latest/tutorial.html)** - Code generation library

### JavaScript/TypeScript
- **[TypeScript Compiler API](https://github.com/Microsoft/TypeScript/wiki/Using-the-Compiler-API)** - Understanding TypeScript's compiler
- **[Babel Plugin Development](https://github.com/jamiebuilds/babel-handbook)** - JavaScript transformation
- **[Build a JavaScript Compiler](https://the-super-tiny-compiler.glitch.me/)** - Interactive tutorial

### Java
- **[ANTLR Tutorial](https://github.com/antlr/antlr4/blob/master/doc/getting-started.md)** - Parser generator for Java
- **[Java Compiler API](https://docs.oracle.com/javase/8/docs/api/javax/tools/JavaCompiler.html)** - Built-in compilation
- **[Eclipse JDT Compiler](https://www.eclipse.org/jdt/core/)** - Production Java compiler

### Haskell
- **[GHC Developer Guide](https://gitlab.haskell.org/ghc/ghc/-/wikis/building)** - Glasgow Haskell Compiler
- **[Implementing Functional Languages](http://research.microsoft.com/en-us/um/people/simonpj/Papers/pj-lester-book/)** - Simon Peyton Jones' book
- **[Write You a Haskell](http://dev.stephendiehl.com/fun/)** - Stephen Diehl's compiler tutorial

## 🏗️ Project Ideas

### Beginner Projects
1. **Expression Compiler** - Arithmetic expressions to assembly
2. **Stack Machine Compiler** - Postfix notation compiler
3. **Brainfuck Compiler** - Simple language to machine code

### Intermediate Projects
1. **C Subset Compiler** - Basic C language features
2. **Functional Language Compiler** - Lambda calculus compilation
3. **SQL Query Compiler** - Database query optimization

### Advanced Projects
1. **LLVM Frontend** - Language frontend using LLVM
2. **JIT Compiler** - Runtime code generation
3. **Optimizing Compiler** - Advanced optimization passes

## ⚙️ Core Concepts

### Compiler Phases
- **Frontend**: Lexical analysis, parsing, semantic analysis
- **Middle-end**: Intermediate representation, optimization
- **Backend**: Register allocation, code generation
- **Linking**: Combining object files into executables

### Optimization Techniques
- **Constant Folding**: Compile-time expression evaluation
- **Dead Code Elimination**: Removing unreachable code
- **Loop Optimization**: Unrolling, invariant motion
- **Register Allocation**: Efficient register usage

### Target Architectures
- **RISC vs CISC**: Instruction set design trade-offs
- **Stack Machines**: Virtual machine architectures
- **Register Machines**: Physical processor targets
- **Virtual Machines**: Intermediate execution models

## 🚀 Performance Optimization

### Frontend Optimization
- **Incremental Parsing**: Reusing parse results
- **Symbol Table**: Efficient name resolution
- **Error Recovery**: Graceful error handling
- **Parallel Parsing**: Multi-threaded compilation

### Backend Optimization
- **Instruction Selection**: Optimal instruction matching
- **Peephole Optimization**: Local code improvements
- **Global Optimization**: Cross-function analysis
- **Profile-Guided Optimization**: Runtime feedback

### Advanced Techniques
- **Whole Program Analysis**: Global optimization
- **Link-Time Optimization**: Cross-module optimization
- **Just-In-Time Compilation**: Runtime optimization
- **Adaptive Compilation**: Dynamic optimization

## 🧪 Testing Strategies

### Unit Testing
- **Lexer Tests**: Token generation validation
- **Parser Tests**: AST construction verification
- **Semantic Tests**: Type checking and scoping
- **Code Generation**: Instruction sequence validation

### Integration Testing
- **End-to-End Compilation**: Source to executable
- **Regression Testing**: Preventing code quality degradation
- **Performance Testing**: Compilation speed benchmarks
- **Correctness Testing**: Output validation

### Compiler Testing
- **Test Suites**: Comprehensive language testing
- **Fuzzing**: Random input generation
- **Differential Testing**: Comparing compiler outputs
- **Formal Verification**: Mathematical correctness proofs

## 🔗 Additional Resources

### Books
- [Compilers: Principles, Techniques, and Tools](https://www.amazon.com/Compilers-Principles-Techniques-Tools-2nd/dp/0321486811) - Dragon Book classic
- [Modern Compiler Implementation](https://www.cs.princeton.edu/~appel/modern/) - Andrew Appel's series
- [Engineering a Compiler](https://www.amazon.com/Engineering-Compiler-Keith-Cooper/dp/012088478X) - Cooper and Torczon
- [Advanced Compiler Design and Implementation](https://www.amazon.com/Advanced-Compiler-Design-Implementation-Muchnick/dp/1558603204) - Steven Muchnick

### Online Resources
- [LLVM Documentation](https://llvm.org/docs/) - Modern compiler infrastructure
- [GCC Internals](https://gcc.gnu.org/onlinedocs/gccint/) - GNU Compiler Collection
- [Compiler Explorer](https://godbolt.org/) - Online compiler output analysis
- [Stanford CS143](http://web.stanford.edu/class/cs143/) - Compiler course materials

### Development Tools
- [ANTLR](https://www.antlr.org/) - Parser generator
- [Yacc/Bison](https://www.gnu.org/software/bison/) - Parser generators
- [Lex/Flex](https://github.com/westes/flex) - Lexical analyzer generators
- [MLIR](https://mlir.llvm.org/) - Multi-level intermediate representation

### Development Communities
- [/r/Compilers](https://www.reddit.com/r/Compilers/) - Compiler development discussions
- [LLVM Community](https://llvm.org/community/) - LLVM development and support
- [Programming Language Design](https://cs.stackexchange.com/questions/tagged/programming-languages) - Academic discussions
- [Compiler Development Discord](https://discord.gg/compiler-dev) - Real-time compiler discussions

---

**Ready to compile?** Start with a simple expression compiler and work your way up to full language implementations!