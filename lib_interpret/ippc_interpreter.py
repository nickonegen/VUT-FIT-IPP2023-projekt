"""
Implementácia triedy interprétu IPPcode23.
@author: Filip J. Kramec <xkrame00@vutbr.cz>
"""

import sys
import xml.etree.ElementTree as ET  # skipcq: BAN-B405
from lib_interpret.ippc_utils import *


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
        self.instructions: list[Instruction] = []
        self.program_counter: int = 0
        self.frames = {"global": Frame(), "temporary": None}
        self.call_stack = Stack()
        self.data_stack = Stack()
        self.frame_stack = Stack()
        self.input_queue = Queue()
        self.labels: dict[str, int] = {}
        self._verbose = False
        self.parse_xml(xml)

        for line in in_txt.splitlines():
            self.input_queue.enqueue(line)

    def __repr__(self):
        lines = [
            "#############################",
            "# START OF INTERPRETER DUMP #",
            f"  Program counter: {self.program_counter}",
            f"    No. of instructions: {len(self.instructions)}",
            f"  Frame stack size: {self.frame_stack.size()}",
            f"    TF exists: {self.frames['temporary'] is not None}",
            f"  Data stack size: {self.data_stack.size()}",
            f"  Input queue size: {self.input_queue.size()}",
            "",
            f"Global frame variables: ({self.frames['global'].size()})",
            f"{self.frames['global']}",
            f"Data stack: ({self.data_stack.size()})",
            f"{self.data_stack}",
            f"Input queue: ({self.input_queue.size()})",
            f"{self.input_queue}",
            f"Labels: ({len(self.labels)})",
            *(f"    {k} = {v}" for k, v in self.labels.items()),
            "",
            f"Instructions: ({len(self.instructions)})",
            *(
                f"    {('> ' if index == self.program_counter else '  ')}{instruction}"
                for index, instruction in enumerate(self.instructions)
            ),
            "",
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

        def validate_xml_root(xml):
            if xml.tag != "program" or xml.attrib["language"] != "IPPcode23":
                raise KeyError("Invalid XML root element")

        def parse_xml_element(instr_elm):
            """Spracuje jeden element (inštrukciu) XML reprezentácie"""
            if instr_elm.tag != "instruction":
                raise KeyError(f"Unexpected element {instr_elm.tag}")
            order = int(instr_elm.attrib["order"])
            if order < 1:
                raise KeyError("Invalid instruction order")
            opcode = instr_elm.attrib["opcode"].upper()
            operands_dict = {
                int(arg_elm.tag[-1]): parse_operand(arg_elm)
                for arg_elm in instr_elm
                if arg_elm.tag in ["arg1", "arg2", "arg3"]
            }

            if len(operands_dict) != len(instr_elm):
                raise KeyError("Duplicate or missing arguments")
            for i in range(1, len(operands_dict) + 1):
                if i not in operands_dict:
                    raise KeyError(f"Missing argument {i}")

            operands = [operands_dict[i] for i in sorted(operands_dict)]
            return order, Instruction(opcode, operands)

        xml = ET.fromstring(xml_str)  # skipcq: BAN-B314
        validate_xml_root(xml)

        temp_instructions = {}
        for instr_elm in xml:
            order, instruction = parse_xml_element(instr_elm)
            if order in temp_instructions:
                raise KeyError(f"Duplicate instruction order {order}")
            temp_instructions[order] = instruction

        for order, instruction in sorted(temp_instructions.items()):
            self.instructions.append(instruction)
            if instruction.opcode == "LABEL":
                label_name = instruction.operands[0].name
                if label_name in self.labels:
                    raise KeyError(f"Duplicate label {label_name}")
                self.labels[label_name] = len(self.instructions) - 1

    def peek_instruction(self):
        """Vráti inštrukciu, ktorá bude spracovaná ďalšia"""
        if len(self.instructions) <= self.program_counter:
            return None
        return self.instructions[self.program_counter]

    def make_verbose(self):
        """Zapne výpisovanie všetkých inštrukcií"""
        self._verbose = True

    def get_frame(self, name: str):
        """Vráti dátový rámec podľa názvu"""
        frame = None
        nameu = name.upper()
        if nameu == "GF":
            frame = self.frames["global"]
        elif nameu == "TF":
            frame = self.frames["temporary"]
            if frame is None:
                raise MemoryError("Attempt to access non-existent TF")
        elif nameu == "LF":
            frame = self.frame_stack.top()
            if frame is None:
                raise MemoryError("Attempt to access non-existent LF")
        else:
            raise AttributeError("Invalid frame name")

        if frame is None:
            raise AttributeError("Invalid frame name")
        return frame

    def execute_next(self):
        """Vykoná jednu inštrukciu a vráti jej prípadnú návratovú hodnotu"""

        def validate_operand(operand, expected_type: str):
            if operand is None:
                raise RuntimeError(f"Unresolvable operand {operand}")

            if isinstance(operand, Value):
                if expected_type in ("value", "symb"):
                    return operand
                if operand.type != expected_type:
                    raise TypeError(
                        f"Unexpected operand type {operand.type}, {expected_type} expected"
                    )
                return operand
            if isinstance(operand, UnresolvedVariable):
                if expected_type not in ("var", "symb"):
                    raise TypeError(
                        f"Unexpected operand typ {operand.type}, {expected_type} expected"
                    )
                return operand
            if isinstance(operand, LabelArg):
                if expected_type != "label":
                    raise TypeError(
                        f"Unexpected operand type {operand.type}, {expected_type} expected"
                    )
                if operand.name not in self.labels:
                    raise RuntimeError(f"Undefined label {operand.name}")
                return operand
            raise RuntimeError(f"Unresolvable operand {operand}")

        def resolve_symb(symb, expected_type="value"):
            result = None
            if isinstance(symb, Value):
                result = symb
            if isinstance(symb, UnresolvedVariable):
                frame = self.get_frame(symb.frame)
                result = frame.get_variable(symb.name)
            if result is None:
                raise IndexError(f"Invalid symbol {symb}")
            validate_operand(result, expected_type)
            return result

        def check_opcount(expected_count: int) -> bool:
            if len(instr.operands) != expected_count:
                raise RuntimeError(
                    f"Wrong number of operands {len(instr.operands)}, {expected_count} expected"
                )
            return True

        def check_stacklen(size: int) -> bool:
            if self.data_stack.size() < size:
                raise IndexError("Stack underflow")
            return True

        def _dbgprint_variable(var, val):
            if self._verbose:
                print(
                    f"    \033[32m{var.frame}@\033[0m{var.name} = \033[33m{val}\033[0m"
                )

        def _dbgprint_value(val):
            if self._verbose:
                print(f"    \033[33m{val}\033[0m")

        def _dbgprint_stacktop():
            if self._verbose:
                print(
                    f"    {{\033[33m{self.data_stack.top().pyv() if not self.data_stack.is_empty() else  'NULL'}\033[0m}}"
                )

        if self.program_counter >= len(self.instructions):
            return 0

        instr: Instruction = self.instructions[self.program_counter]

        if self._verbose:
            print(f"  \033[90m{instr}\033[0m")

        opcode_impl = {}

        def execute_MOVE():
            """MOVE (var)targ (symb)val"""
            check_opcount(2)
            targ, val = instr.operands
            validate_operand(targ, "var")
            validate_operand(val, "symb")
            val = resolve_symb(val)
            self.get_frame(targ.frame).set_variable(targ.name, val)
            _dbgprint_variable(targ, val.pyv())

        opcode_impl["MOVE"] = execute_MOVE

        def execute_CREATEFRAME():
            """CREATEFRAME"""
            check_opcount(0)
            self.frames["temporary"] = Frame()

        opcode_impl["CREATEFRAME"] = execute_CREATEFRAME

        def execute_PUSHFRAME():
            """PUSHFRAME"""
            check_opcount(0)
            if self.frames["temporary"] is None:
                raise MemoryError("Attempt to push non-existent TF")
            self.frame_stack.push(self.frames["temporary"])
            self.frames["temporary"] = None

        opcode_impl["PUSHFRAME"] = execute_PUSHFRAME

        def execute_POPFRAME():
            """POPFRAME"""
            check_opcount(0)
            if self.frame_stack.is_empty():
                raise MemoryError("Attempt to pop non-existent LF")
            self.frames["temporary"] = self.frame_stack.pop()

        opcode_impl["POPFRAME"] = execute_POPFRAME

        def execute_DEFVAR():
            """DEFVAR (var)var"""
            check_opcount(1)
            var = validate_operand(instr.operands[0], "var")
            self.get_frame(var.frame).define_variable(var.name)
            _dbgprint_variable(var, "[defined]")

        opcode_impl["DEFVAR"] = execute_DEFVAR

        def execute_CALL():
            """CALL (label)label"""
            check_opcount(1)
            label = validate_operand(instr.operands[0], "label")
            self.call_stack.push(self.program_counter + 1)
            self.program_counter = self.labels[label.name]

        opcode_impl["CALL"] = execute_CALL

        def execute_RETURN():
            """RETURN"""
            check_opcount(0)
            if self.call_stack.is_empty():
                raise IndexError("Empty call stack, nothing to return to")
            self.program_counter = self.call_stack.pop() - 1

        opcode_impl["RETURN"] = execute_RETURN

        def execute_PUSHS():
            """PUSHS (symb)val"""
            check_opcount(1)
            val = validate_operand(instr.operands[0], "symb")
            self.data_stack.push(resolve_symb(val))
            _dbgprint_stacktop()

        opcode_impl["PUSHS"] = execute_PUSHS

        def execute_POPS():
            """POPS (var)targ"""
            check_opcount(1)
            targ = validate_operand(instr.operands[0], "var")
            check_stacklen(1)
            val = self.data_stack.pop()
            self.get_frame(targ.frame).set_variable(targ.name, val)
            _dbgprint_variable(targ, val.pyv())
            _dbgprint_stacktop()

        opcode_impl["POPS"] = execute_POPS

        def execute_CLEARS():
            """CLEARS"""
            check_opcount(0)
            self.data_stack.clear()
            _dbgprint_stacktop()

        opcode_impl["CLEARS"] = execute_CLEARS

        def execute_ADD():
            """ADD (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            result = resolve_symb(val1) + resolve_symb(val2)
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, result.pyv())

        opcode_impl["ADD"] = execute_ADD

        def execute_SUB():
            """SUB (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            result = resolve_symb(val1) - resolve_symb(val2)
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, result.pyv())

        opcode_impl["SUB"] = execute_SUB

        def execute_MUL():
            """MUL (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            result = resolve_symb(val1) * resolve_symb(val2)
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, result.pyv())

        opcode_impl["MUL"] = execute_MUL

        def execute_DIV():
            """DIV (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            result = resolve_symb(val1) / resolve_symb(val2)
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, result.pyv())

        opcode_impl["DIV"] = execute_DIV

        def execute_IDIV():
            """IDIV (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            validate_operand(targ, "symb")
            validate_operand(targ, "symb")
            result = resolve_symb(val1) // resolve_symb(val2)
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, result.pyv())

        opcode_impl["IDIV"] = execute_IDIV

        def execute_ADDS():
            """ADDS"""
            check_opcount(0)
            check_stacklen(2)
            val2, val1 = self.data_stack.pop(), self.data_stack.pop()
            self.data_stack.push(val1 + val2)
            _dbgprint_stacktop()

        opcode_impl["ADDS"] = execute_ADDS

        def execute_SUBS():
            """SUBS"""
            check_opcount(0)
            check_stacklen(2)
            val2, val1 = self.data_stack.pop(), self.data_stack.pop()
            self.data_stack.push(val1 - val2)
            _dbgprint_stacktop()

        opcode_impl["SUBS"] = execute_SUBS

        def execute_MULS():
            """MULS"""
            check_opcount(0)
            check_stacklen(2)
            val2, val1 = self.data_stack.pop(), self.data_stack.pop()
            self.data_stack.push(val1 * val2)
            _dbgprint_stacktop()

        opcode_impl["MULS"] = execute_MULS

        def execute_DIVS():
            """DIVS"""
            check_opcount(0)
            check_stacklen(2)
            val2, val1 = self.data_stack.pop(), self.data_stack.pop()
            self.data_stack.push(val1 / val2)
            _dbgprint_stacktop()

        opcode_impl["DIVS"] = execute_DIVS

        def execute_IDIVS():
            """IDIVS"""
            check_opcount(0)
            check_stacklen(2)
            val2, val1 = self.data_stack.pop(), self.data_stack.pop()
            self.data_stack.push(val1 // val2)
            _dbgprint_stacktop()

        opcode_impl["IDIVS"] = execute_IDIVS

        def execute_LT():
            """LT (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            result = resolve_symb(val1) < resolve_symb(val2)
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, result.pyv())

        opcode_impl["LT"] = execute_LT

        def execute_GT():
            """GT (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            result = resolve_symb(val1) > resolve_symb(val2)
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, result.pyv())

        opcode_impl["GT"] = execute_GT

        def execute_EQ():
            """EQ (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            result = resolve_symb(val1) == resolve_symb(val2)
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, result.pyv())

        opcode_impl["EQ"] = execute_EQ

        def execute_LTS():
            """LTS"""
            check_opcount(0)
            check_stacklen(2)
            val2, val1 = self.data_stack.pop(), self.data_stack.pop()
            self.data_stack.push(val1 < val2)
            _dbgprint_stacktop()

        opcode_impl["LTS"] = execute_LTS

        def execute_GTS():
            """GTS"""
            check_opcount(0)
            check_stacklen(2)
            val2, val1 = self.data_stack.pop(), self.data_stack.pop()
            self.data_stack.push(val1 > val2)
            _dbgprint_stacktop()

        opcode_impl["GTS"] = execute_GTS

        def execute_EQS():
            """EQS"""
            check_opcount(0)
            check_stacklen(2)
            val2, val1 = self.data_stack.pop(), self.data_stack.pop()
            self.data_stack.push(val1 == val2)
            _dbgprint_stacktop()

        opcode_impl["EQS"] = execute_EQS

        def execute_AND():
            """AND (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            result = resolve_symb(val1, "bool") & resolve_symb(val2, "bool")
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, result.pyv())

        opcode_impl["AND"] = execute_AND

        def execute_OR():
            """OR (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            result = resolve_symb(val1, "bool") | resolve_symb(val2, "bool")
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, result.pyv())

        opcode_impl["OR"] = execute_OR

        def execute_NOT():
            """NOT (var)targ (symb)val"""
            check_opcount(2)
            targ, val = instr.operands
            validate_operand(targ, "var")
            validate_operand(val, "symb")
            result = ~resolve_symb(val, "bool")
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, result.pyv())

        opcode_impl["NOT"] = execute_NOT

        def execute_ANDS():
            """ANDS"""
            check_opcount(0)
            check_stacklen(2)
            val2, val1 = self.data_stack.pop(), self.data_stack.pop()
            self.data_stack.push(val1 & val2)
            _dbgprint_stacktop()

        opcode_impl["ANDS"] = execute_ANDS

        def execute_ORS():
            """ORS"""
            check_opcount(0)
            check_stacklen(2)
            val2, val1 = self.data_stack.pop(), self.data_stack.pop()
            self.data_stack.push(val1 | val2)
            _dbgprint_stacktop()

        opcode_impl["ORS"] = execute_ORS

        def execute_NOTS():
            """NOTS"""
            check_opcount(0)
            check_stacklen(1)
            val = self.data_stack.pop()
            self.data_stack.push(~val)
            _dbgprint_stacktop()

        opcode_impl["NOTS"] = execute_NOTS

        def execute_INT2FLOAT():
            """INT2FLOAT (var)targ (symb)val"""
            check_opcount(2)
            targ, val = instr.operands
            validate_operand(targ, "var")
            validate_operand(val, "symb")
            val = resolve_symb(val, "int").to_type("float")
            self.get_frame(targ.frame).set_variable(targ.name, val)
            _dbgprint_variable(targ, val.pyv())

        opcode_impl["INT2FLOAT"] = execute_INT2FLOAT

        def execute_FLOAT2INT():
            """FLOAT2INT (var)targ (symb)val"""
            check_opcount(2)
            targ, val = instr.operands
            validate_operand(targ, "var")
            validate_operand(val, "symb")
            val = resolve_symb(val, "float").to_type("int")
            self.get_frame(targ.frame).set_variable(targ.name, val)
            _dbgprint_variable(targ, val.pyv())

        opcode_impl["FLOAT2INT"] = execute_FLOAT2INT

        def execute_INT2CHAR():
            """INT2CHAR (var)targ (symb)val"""
            check_opcount(2)
            targ, val = instr.operands
            validate_operand(targ, "var")
            validate_operand(val, "symb")
            val = resolve_symb(val, "int").to_type("string")
            self.get_frame(targ.frame).set_variable(targ.name, val)
            _dbgprint_variable(targ, val.pyv())

        opcode_impl["INT2CHAR"] = execute_INT2CHAR

        def execute_STRI2INT():
            """STRI2INT (var)targ (symb)val (symb)idx"""
            check_opcount(3)
            targ, val, idx = instr.operands
            validate_operand(targ, "var")
            validate_operand(val, "symb")
            validate_operand(idx, "symb")
            idx = resolve_symb(idx, "int")
            val = resolve_symb(val, "string").to_type("int", idx.pyv())
            self.get_frame(targ.frame).set_variable(targ.name, val)
            _dbgprint_variable(targ, val.pyv())

        opcode_impl["STRI2INT"] = execute_STRI2INT

        def execute_INT2FLOATS():
            """INT2FLOATS"""
            check_opcount(0)
            check_stacklen(1)
            val = self.data_stack.pop()
            validate_operand(val, "int")
            val = val.to_type("float")
            self.data_stack.push(val)
            _dbgprint_stacktop()

        opcode_impl["INT2FLOATS"] = execute_INT2FLOATS

        def execute_FLOAT2INTS():
            """FLOAT2INTS"""
            check_opcount(0)
            check_stacklen(1)
            val = self.data_stack.pop()
            validate_operand(val, "float")
            val = val.to_type("int")
            self.data_stack.push(val)
            _dbgprint_stacktop()

        opcode_impl["FLOAT2INTS"] = execute_FLOAT2INTS

        def execute_INT2CHARS():
            """INT2CHARS"""
            check_opcount(0)
            check_stacklen(1)
            val = self.data_stack.pop()
            validate_operand(val, "int")
            val = val.to_type("string")
            self.data_stack.push(val)
            _dbgprint_stacktop()

        opcode_impl["INT2CHARS"] = execute_INT2CHARS

        def execute_STRI2INTS():
            """STRI2INTS"""
            check_opcount(0)
            check_stacklen(2)
            idx, val = self.data_stack.pop(), self.data_stack.pop()
            validate_operand(val, "string")
            validate_operand(idx, "int")
            val = val.to_type("int", idx.pyv())
            self.data_stack.push(val)
            _dbgprint_stacktop()

        opcode_impl["STRI2INTS"] = execute_STRI2INTS

        def execute_READ():
            """READ (var)targ (type)ttype"""
            check_opcount(2)
            targ, ttype = instr.operands
            validate_operand(targ, "var")
            validate_operand(ttype, "type")
            try:
                val = (
                    Value("nil", "")
                    if self.input_queue.is_empty()
                    else Value(ttype.pyv(), str(self.input_queue.dequeue()))
                )
            except Exception:  # skipcq: PYL-W0703
                val = Value("nil", "")
            self.get_frame(targ.frame).set_variable(targ.name, val)
            _dbgprint_variable(targ, val.pyv())

        opcode_impl["READ"] = execute_READ

        def execute_WRITE():
            """WRITE (symb)val"""
            check_opcount(1)
            val = validate_operand(instr.operands[0], "symb")
            print(str(resolve_symb(val)), end="")
            if self._verbose:
                print("")

        opcode_impl["WRITE"] = execute_WRITE

        def execute_CONCAT():
            """CONCAT (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            result = str(resolve_symb(val1, "string")) + str(
                resolve_symb(val2, "string")
            )
            self.get_frame(targ.frame).set_variable(
                targ.name, Value("string", str(result))
            )
            _dbgprint_variable(targ, str(result))

        opcode_impl["CONCAT"] = execute_CONCAT

        def execute_STRLEN():
            """STRLEN (var)targ (symb)val"""
            check_opcount(2)
            targ, val = instr.operands
            validate_operand(targ, "var")
            validate_operand(val, "symb")
            result = Value("int", str(len(str(resolve_symb(val, "string")))))
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, str(result))

        opcode_impl["STRLEN"] = execute_STRLEN

        def execute_GETCHAR():
            """GETCHAR (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            val1, val2 = resolve_symb(val1, "string"), resolve_symb(val2, "int")
            result = val1.to_type("string", val2.pyv())
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, str(result))

        opcode_impl["GETCHAR"] = execute_GETCHAR

        def execute_SETCHAR():
            """SETCHAR (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            tval = resolve_symb(targ, "string")
            val1, val2 = resolve_symb(val1, "int"), resolve_symb(val2, "string")
            tval.to_type("string", val1.pyv())  # Overí index
            try:
                tlist = list(str(tval))
                tlist[val1.pyv()] = str(val2)[0]
                result = Value("string", "".join(tlist))
            except Exception:  # skipcq: PYL-W0703
                raise NameError("Invalid index")
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, str(result))

        opcode_impl["SETCHAR"] = execute_SETCHAR

        def execute_TYPE():
            """TYPE (var)targ (symb)val"""
            check_opcount(2)
            targ, val = instr.operands
            validate_operand(targ, "var")
            validate_operand(val, "symb")
            try:
                val = resolve_symb(val)
                result = Value("string", val.type)
            except IndexError:
                val = Value("nil", "")
                result = Value("string", "")
            self.get_frame(targ.frame).set_variable(targ.name, result)
            _dbgprint_variable(targ, str(result))

        opcode_impl["TYPE"] = execute_TYPE

        def execute_LABEL():
            """LABEL (label)label"""
            check_opcount(1)  # Náveštie rieši XML parser

        opcode_impl["LABEL"] = execute_LABEL

        def execute_JUMP():
            """JUMP (label)label"""
            check_opcount(1)
            label = instr.operands[0]
            validate_operand(label, "label")
            self.program_counter = self.labels[label.name]

        opcode_impl["JUMP"] = execute_JUMP

        def execute_JUMPIFEQ():
            """JUMPIFEQ (label)label (symb)val1 (symb)val2"""
            check_opcount(3)
            label, val1, val2 = instr.operands
            validate_operand(label, "label")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            val1, val2 = resolve_symb(val1), resolve_symb(val2)
            dojump = (val1 == val2).pyv()
            if dojump:
                self.program_counter = self.labels[label.name]
            _dbgprint_value(str(dojump).lower())

        opcode_impl["JUMPIFEQ"] = execute_JUMPIFEQ

        def execute_JUMPIFNEQ():
            """JUMPIFNEQ (label)label (symb)val1 (symb)val2"""
            check_opcount(3)
            label, val1, val2 = instr.operands
            validate_operand(label, "label")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            val1, val2 = resolve_symb(val1), resolve_symb(val2)
            dojump = (val1 != val2).pyv()
            if dojump:
                self.program_counter = self.labels[label.name]
            _dbgprint_value(str(dojump).lower())

        opcode_impl["JUMPIFNEQ"] = execute_JUMPIFNEQ

        def execute_JUMPIFEQS():
            """JUMPIFEQS (label)label"""
            check_opcount(1)
            label = validate_operand(instr.operands[0], "label")
            check_stacklen(2)
            dojump = (self.data_stack.pop() == self.data_stack.pop()).pyv()
            if dojump:
                self.program_counter = self.labels[label.name]
            _dbgprint_value(str(dojump).lower())

        opcode_impl["JUMPIFEQS"] = execute_JUMPIFEQS

        def execute_JUMPIFNEQS():
            """JUMPIFNEQS (label)label"""
            check_opcount(1)
            label = validate_operand(instr.operands[0], "label")
            check_stacklen(2)
            dojump = (self.data_stack.pop() != self.data_stack.pop()).pyv()
            if dojump:
                self.program_counter = self.labels[label.name]
            _dbgprint_value(str(dojump).lower())

        opcode_impl["JUMPIFNEQS"] = execute_JUMPIFNEQS

        def execute_EXIT():
            """EXIT (symb)val"""
            check_opcount(1)
            val = validate_operand(instr.operands[0], "symb")
            val = resolve_symb(val, "int")
            if 0 <= val.pyv() <= 49:
                _dbgprint_value(val.pyv())
                return val.content
            raise ValueError("Invalid exit code")

        opcode_impl["EXIT"] = execute_EXIT

        def execute_DPRINT():
            """DPRINT (symb)val"""
            check_opcount(1)
            val = validate_operand(instr.operands[0], "symb")
            val = resolve_symb(val)
            print(str(val), file=sys.stderr, end="")

        opcode_impl["DPRINT"] = execute_DPRINT

        def execute_BREAK():
            """BREAK"""
            check_opcount(0)
            print(repr(self), file=sys.stderr)

        opcode_impl["BREAK"] = execute_BREAK

        iexecute = opcode_impl.get(instr.opcode)
        if not iexecute:
            raise RuntimeError("Unrecognised instruction")
        retcode = iexecute()
        self.program_counter += 1
        return retcode
