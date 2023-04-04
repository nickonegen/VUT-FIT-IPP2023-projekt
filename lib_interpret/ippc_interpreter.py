"""
Implementácia triedy interprétu IPPcode23.
@author: Onegen Something <xonege99@vutbr.cz>
"""

import xml.etree.ElementTree as ET  # skipcq: BAN-B405
from lib_interpret.ippc_idata import Stack, Queue
from lib_interpret.ippc_icontrol import (
    Frame,
    Instruction,
    LabelArg,
    UnresolvedVariable,
    Value,
)


class Interpreter:
    """
    Trieda reprezentujúca celkový interpret jazyka IPPcode23.

    Atribúty:
        instructions (list): zoznam všetkých instrukcií
        program_counter (int): počítadlo spracovaných inštrukcií
        frames (dict): slovník dátových rámcov
        frame_stack (Stack): zásobník dátových rámcov (vrchol = LF)
        data_stack (Stack): zásobník dátových hodnôt
        input_queue (Queue): fronta vstupných hodnôt
        labels (dict): slovník náveští
    """

    def __init__(self, xml, in_txt):
        self.instructions = Queue()
        self.program_counter = 0
        self.frames = {"global": Frame(), "temporary": None}
        self.frame_stack = Stack()
        self.data_stack = Stack()
        self.input_queue = Queue()
        self.labels = {}
        self.parse_xml(xml)

        for line in in_txt.splitlines():
            self.input_queue.enqueue(line)

    def __repr__(self):
        lines = [
            "#############################",
            "# START OF INTERPRETER DUMP #",
            f"  Program counter: {self.program_counter}",
            f"    All instructions: {self.program_counter + self.instructions.size()}",
            f"  Frame stack size: {self.frame_stack.size()}",
            f"    TF exists: {self.frames['temporary'] is not None}",
            f"  Data stack size: {self.data_stack.size()}",
            f"  Input queue size: {self.input_queue.size()}",
            "",
            f"Global frame variables: ({self.frames['global'].size()})",
            f"{self.frames['global']}",
            "",
            f"Data stack: ({self.data_stack.size()})",
            f"{self.data_stack}",
            "",
            f"Input queue: ({self.input_queue.size()})",
            f"{self.input_queue}",
            "",
            f"Labels: ({len(self.labels)})",
            *(f"    {k} = {v}" for k, v in self.labels.items()),
            "",
            f"Instruction queue: ({self.instructions.size()})",
            f"{self.instructions}",
            "# END OF INTERPRETER DUMP #",
            "###########################",
        ]

        return "\n".join(lines)

    def parse_xml(self, xml_str):
        """Spracuje XML reprezentácie programu"""

        def parse_operand(arg_elm):
            type_mapping = {
                "int": Value,
                "string": Value,
                "bool": Value,
                "float": Value,
                "type": Value,
                "nil": Value,
                "var": lambda _, v: UnresolvedVariable(v),
                "label": lambda _, v: LabelArg(v),
            }
            arg_type = arg_elm.attrib["type"]
            constructor = type_mapping.get(arg_type)
            if constructor is None:
                raise KeyError(f"Invalid argument type {arg_type}")
            return constructor(arg_type, arg_elm.text)

        def _parse_xml_element(instr_elm):
            """Spracuje jeden element (inštrukciu) XML reprezentácie"""
            order = int(instr_elm.attrib["order"])
            opcode = instr_elm.attrib["opcode"].upper()
            operands = [
                parse_operand(arg_elm)
                for arg_elm in instr_elm
                if arg_elm.tag in ["arg1", "arg2", "arg3"]
            ]
            return order, Instruction(opcode, operands)

        xml = ET.fromstring(xml_str)  # skipcq: BAN-B314
        if xml.tag != "program" or xml.attrib["language"] != "IPPcode23":
            raise KeyError("Invalid XML root element")

        temp_instructions = {
            order: instruction
            for order, instruction in (
                _parse_xml_element(instr_elm)
                for instr_elm in xml
                if instr_elm.tag == "instruction"
            )
        }

        for order, instruction in sorted(temp_instructions.items()):
            if instruction.opcode == "LABEL":
                self.labels[instruction.operands[0].name] = order
            self.instructions.enqueue(instruction)

    def peek_instruction(self):
        """Vráti inštrukciu na vrchu zoznamu inštrukcií"""
        return self.instructions.top()

    def get_frame(self, name):
        """Vráti dátový rámec podľa názvu"""
        match name.upper():
            case "GF":
                return self.frames["global"]
            case "TF":
                if self.frames["temporary"] is None:
                    raise MemoryError("Attempted to access non-existent TF")
                return self.frames["temporary"]
            case "LF":
                if self.frame_stack.is_empty():
                    raise MemoryError("Attempted to access non-existent LF")
                return self.frame_stack.top()
            case "_":
                raise AttributeError("Invalid frame name")

    def execute_next(self):
        """Vykoná jednu inštrukciu a vráti jej návratovú hodnotu (default 0)"""

        def validate_operand(instr_name, operand, expected_type):
            if operand is None:
                raise RuntimeError(f"Bad number of {instr_name} operands")

            if isinstance(operand, Value):
                if expected_type in ("value", "symb"):
                    return True
                if operand.type != expected_type:
                    raise TypeError(
                        f"{instr_name} expected {expected_type}, got {operand.type}"
                    )
                return True
            if isinstance(operand, UnresolvedVariable):
                if expected_type not in ("var", "symb"):
                    raise TypeError(f"{instr_name} requires {expected_type}")
                return True
            if isinstance(operand, LabelArg):
                if expected_type != "label":
                    raise TypeError(f"{instr_name} requires {expected_type}")
                return True
            raise RuntimeError(f"{operand} is not a valid operand")

        def resolve_symb(symb):
            if isinstance(symb, Value):
                return symb
            if isinstance(symb, UnresolvedVariable):
                frame = self.get_frame(symb.frame)
                return frame.get_variable(symb.name)
            raise RuntimeError(f"{symb} is not a valid symbol")

        def check_opcount(expected_count):
            if len(instr.operands) != expected_count:
                raise RuntimeError(
                    f"{instr_name} needs {expected_count} operands, got {len(instr.operands)}"
                )

        if self.instructions.is_empty():
            return -1

        self.program_counter += 1
        instr = self.instructions.dequeue()
        instr_name = instr.opcode.upper()

        def execute_DEFVAR():
            """DEFVAR var"""
            check_opcount(1)
            [var] = instr.operands
            validate_operand(instr_name, var, "var")
            frame = self.get_frame(var.frame)
            frame.define_variable(var.name)

        def execute_READ():
            """READ targ ttype"""
            check_opcount(2)
            [targ, ttype] = instr.operands
            validate_operand(instr_name, targ, "var")
            validate_operand(instr_name, ttype, "type")
            value = Value(ttype.content, self.input_queue.dequeue())
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, value)

        def execute_WRITE():
            """WRITE val"""
            check_opcount(1)
            [val] = instr.operands
            validate_operand(instr_name, val, "symb")
            val = resolve_symb(val)
            print(str(val), end="")

        opcode_impl = {
            "DEFVAR": execute_DEFVAR,
            "READ": execute_READ,
            "WRITE": execute_WRITE,
        }

        iexecute = opcode_impl.get(instr.opcode)
        if iexecute:
            iexecute()
        else:
            raise NotImplementedError(f"Unknown instruction: {instr.opcode}")
