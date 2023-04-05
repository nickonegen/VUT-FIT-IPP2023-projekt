"""
Implementácia triedy interprétu IPPcode23.
@author: Onegen Something <xonege99@vutbr.cz>
"""

import sys
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

    def parse_xml(self, xml_str: str):
        """Spracuje XML reprezentácie programu"""

        def parse_operand(arg_elm: ET.Element) -> Value | UnresolvedVariable | LabelArg:
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

        def _parse_xml_element(instr_elm: ET.Element) -> tuple[int, Instruction]:
            """Spracuje jeden element (inštrukciu) XML reprezentácie"""
            if instr_elm.tag != "instruction":
                raise KeyError(f"Unexpected element: {instr_elm.tag}")
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

            operands = [operands_dict[i] for i in sorted(operands_dict)]
            return order, Instruction(opcode, operands)

        xml = ET.fromstring(xml_str)  # skipcq: BAN-B314
        if xml.tag != "program" or xml.attrib["language"] != "IPPcode23":
            raise KeyError("Invalid XML root element")

        temp_instructions = {}
        for instr_elm in xml:
            order, instruction = _parse_xml_element(instr_elm)
            if order in temp_instructions:
                raise KeyError(f"Duplicate instruction order {order}")
            temp_instructions[order] = instruction

        for order, instruction in sorted(temp_instructions.items()):
            self.instructions.append(instruction)
            if instruction.opcode == "LABEL":
                if instruction.operands[0].name in self.labels:
                    raise KeyError(f"Duplicate label {instruction.operands[0].name}")
                self.labels[instruction.operands[0].name] = len(self.instructions) - 1

    def peek_instruction(self) -> Instruction | None:
        """Vráti inštrukciu, ktorá bude spracovaná ďalšia"""
        if len(self.instructions) <= self.program_counter:
            return None
        return self.instructions[self.program_counter]

    def make_verbose(self):
        """Zapne výpisovanie všetkých inštrukcií"""
        self._verbose = True

    def get_frame(self, name: str) -> Frame:
        """Vráti dátový rámec podľa názvu"""
        frame = None
        match name.upper():
            case "GF":
                frame = self.frames["global"]
            case "TF":
                frame = self.frames["temporary"]
                if frame is None:
                    raise MemoryError("Attempted to access non-existent TF")
            case "LF":
                frame = self.frame_stack.top()
                if frame is None:
                    raise MemoryError("Attempted to access non-existent LF")
            case "_":
                raise AttributeError("Invalid frame name")

        if frame is None:
            raise AttributeError("Invalid frame name")
        return frame

    def execute_next(self) -> int:
        """Vykoná jednu inštrukciu a vráti jej návratovú hodnotu (default 0)"""

        def validate_operand(operand, expected_type: str) -> bool:
            if operand is None:
                raise RuntimeError("Bad number of operands")

            if isinstance(operand, Value):
                if expected_type in ("value", "symb"):
                    return True
                if operand.type != expected_type:
                    raise TypeError(
                        f"Unexpected operand type, expected {expected_type}"
                    )
                return True
            if isinstance(operand, UnresolvedVariable):
                if expected_type not in ("var", "symb"):
                    raise TypeError(
                        f"Unexpected operand type, expected {expected_type}"
                    )
                return True
            if isinstance(operand, LabelArg):
                if expected_type != "label":
                    raise TypeError(
                        f"Unexpected operand type, expected {expected_type}"
                    )
                return True
            raise RuntimeError(f"Invalid operand {operand}")

        def resolve_symb(
            symb: Value | UnresolvedVariable, expected_type="value"
        ) -> Value:
            result = None
            if isinstance(symb, Value):
                result = symb
            if isinstance(symb, UnresolvedVariable):
                frame = self.get_frame(symb.frame)
                result = frame.get_variable(symb.name)
            if result is None:
                raise IndexError(f"{symb} is not a valid defined symbol")
            validate_operand(result, expected_type)
            return result

        def check_opcount(expected_count: int) -> bool:
            if len(instr.operands) != expected_count:
                raise RuntimeError(
                    f"{expected_count} operands required, got {len(instr.operands)}"
                )
            return True

        if self.program_counter >= len(self.instructions):
            return 0

        instr: Instruction = self.instructions[self.program_counter]

        if self._verbose:
            print(f"  \033[90m{instr}\033[0m")

        opcode_impl = {}

        def execute_MOVE():
            """MOVE (var)targ (symb)val"""
            check_opcount(2)
            [targ, val] = instr.operands
            validate_operand(targ, "var")
            validate_operand(val, "symb")
            val = resolve_symb(val)
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, val)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{val}\033[0m"
                )

        opcode_impl["MOVE"] = execute_MOVE

        def execute_CREATEFRAME():
            """CREATEFRAME"""
            check_opcount(0)
            if self.frames.get("temporary") is not None:
                self.frames["temporary"] = None
            self.frames["temporary"] = Frame()

        opcode_impl["CREATEFRAME"] = execute_CREATEFRAME

        def execute_PUSHFRAME():
            """PUSHFRAME"""
            check_opcount(0)
            if self.frames["temporary"] is None:
                raise MemoryError("Attempted to push non-existent TF")
            self.frame_stack.push(self.frames["temporary"])
            self.frames["temporary"] = None

        opcode_impl["PUSHFRAME"] = execute_PUSHFRAME

        def execute_POPFRAME():
            """POPFRAME"""
            check_opcount(0)
            if self.frame_stack.is_empty():
                raise MemoryError("Attempted to pop non-existent LF")
            self.frames["temporary"] = self.frame_stack.pop()

        opcode_impl["POPFRAME"] = execute_POPFRAME

        def execute_DEFVAR():
            """DEFVAR (var)var"""
            check_opcount(1)
            [var] = instr.operands
            validate_operand(var, "var")
            frame = self.get_frame(var.frame)
            frame.define_variable(var.name)
            if self._verbose:
                print(
                    f"    \033[32m{var.frame}@\033[0m{var.name} = \033[33mdefined\033[0m"
                )

        opcode_impl["DEFVAR"] = execute_DEFVAR

        def execute_CALL():
            """CALL (label)label"""
            check_opcount(1)
            [label] = instr.operands
            validate_operand(label, "label")
            if label.name not in self.labels:
                raise RuntimeError(f"Label {label.name} not found")
            self.call_stack.push(self.program_counter + 1)
            self.program_counter = self.labels[label.name]

        opcode_impl["CALL"] = execute_CALL

        def execute_RETURN():
            """RETURN"""
            check_opcount(0)
            if self.call_stack.is_empty():
                raise IndexError("Nothing to return from (empty call stack)")
            self.program_counter = self.call_stack.pop()

        opcode_impl["RETURN"] = execute_RETURN

        def execute_PUSHS():
            """PUSHS (symb)val"""
            check_opcount(1)
            [val] = instr.operands
            validate_operand(val, "symb")
            val = resolve_symb(val)
            self.data_stack.push(val)
            if self._verbose:
                print(f"    pushed \033[33m{val}\033[0m")

        opcode_impl["PUSHS"] = execute_PUSHS

        def execute_POPS():
            """POPS (var)targ"""
            check_opcount(1)
            [targ] = instr.operands
            validate_operand(targ, "var")
            try:
                val = self.data_stack.pop()
            except IndexError:
                raise IndexError("Nothing to pop from (empty data stack)")
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, val)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{val}\033[0m"
                )

        opcode_impl["POPS"] = execute_POPS

        def execute_ADD():
            """ADD (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            val1, val2 = resolve_symb(val1), resolve_symb(val2)
            if not all(operand.type in ("int", "float") for operand in (val1, val2)):
                raise TypeError("Unexpected operand type, expected int or float")
            if val1.type != val2.type:
                raise TypeError("Operand types must be equal for ADD operation")
            rtype = val1.type
            result_cont = val1.content + val2.content
            result_cont = float(result_cont).hex() if rtype == "float" else result_cont
            result = Value(rtype, result_cont)
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["ADD"] = execute_ADD

        def execute_SUB():
            """SUB (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            val1, val2 = resolve_symb(val1), resolve_symb(val2)
            if not all(operand.type in ("int", "float") for operand in (val1, val2)):
                raise TypeError("Unexpected operand type, expected int or float")
            if val1.type != val2.type:
                raise TypeError("Operand types must be equal for ADD operation")
            rtype = val1.type
            result_cont = val1.content - val2.content
            result_cont = float(result_cont).hex() if rtype == "float" else result_cont
            result = Value(rtype, result_cont)
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["SUB"] = execute_SUB

        def execute_MUL():
            """MUL (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            val1, val2 = resolve_symb(val1), resolve_symb(val2)
            if not all(operand.type in ("int", "float") for operand in (val1, val2)):
                raise TypeError("Unexpected operand type, expected int or float")
            if val1.type != val2.type:
                raise TypeError("Operand types must be equal for ADD operation")
            rtype = val1.type
            result_cont = val1.content * val2.content
            result_cont = float(result_cont).hex() if rtype == "float" else result_cont
            result = Value(rtype, result_cont)
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["MUL"] = execute_MUL

        def execute_IDIV():
            """IDIV (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            val1, val2 = resolve_symb(val1), resolve_symb(val2)
            if not all(operand.type in ("int", "float") for operand in (val1, val2)):
                raise TypeError("Unexpected operand type, expected int or float")
            if val1.type != val2.type:
                raise TypeError("Operand types must be equal for ADD operation")
            if float(val2.content) == 0.0:
                raise ValueError("Division by zero")
            rtype = val1.type
            result_cont = val1.content // val2.content
            result_cont = float(result_cont).hex() if rtype == "float" else result_cont
            result = Value(rtype, result_cont)
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["IDIV"] = execute_IDIV

        def execute_DIV():
            """DIV (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            targ, val1, val2 = instr.operands
            validate_operand(targ, "var")
            val1, val2 = resolve_symb(val1), resolve_symb(val2)
            if not all(operand.type in ("int", "float") for operand in (val1, val2)):
                raise TypeError("Unexpected operand type, expected int or float")
            if val1.type != val2.type:
                raise TypeError("Operand types must be equal for ADD operation")
            if float(val2.content) == 0.0:
                raise ValueError("Division by zero")
            result = Value("float", float(val1.content / val2.content).hex())
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["DIV"] = execute_DIV

        def execute_LT():
            """LT (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            [targ, val1, val2] = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            val1 = resolve_symb(val1)
            val2 = resolve_symb(val2, val1.type)
            if val1.type == "nil":
                raise KeyError("Cannot compare nil")
            result = Value("bool", val1.content < val2.content)
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["LT"] = execute_LT

        def execute_GT():
            """GT (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            [targ, val1, val2] = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            val1 = resolve_symb(val1)
            val2 = resolve_symb(val2, val1.type)
            if val1.type == "nil":
                raise KeyError("Cannot compare nil")
            result = Value("bool", val1.content > val2.content)
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["GT"] = execute_GT

        def execute_EQ():
            """EQ (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            [targ, val1, val2] = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            val1 = resolve_symb(val1)
            val2 = resolve_symb(val2, val1.type)
            if val1.type == "nil":
                raise KeyError("Cannot compare nil")
            result = Value("bool", val1.content == val2.content)
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["EQ"] = execute_EQ

        def execute_AND():
            """AND (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            [targ, val1, val2] = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            val1 = resolve_symb(val1, "bool")
            val2 = resolve_symb(val2, "bool")
            result = Value("bool", val1.content and val2.content)
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["AND"] = execute_AND

        def execute_OR():
            """OR (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            [targ, val1, val2] = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            val1 = resolve_symb(val1, "bool")
            val2 = resolve_symb(val2, "bool")
            result = Value("bool", val1.content or val2.content)
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["OR"] = execute_OR

        def execute_NOT():
            """NOT (var)targ (symb)val"""
            check_opcount(2)
            [targ, val] = instr.operands
            validate_operand(targ, "var")
            validate_operand(val, "symb")
            val = resolve_symb(val, "bool")
            result = Value("bool", not val.content)
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["NOT"] = execute_NOT

        def execute_INT2CHAR():
            """INT2CHAR (var)targ (symb)val"""
            check_opcount(2)
            [targ, val] = instr.operands
            validate_operand(targ, "var")
            validate_operand(val, "symb")
            val = resolve_symb(val, "int")
            try:
                result = Value("string", chr(val.content))
            except ValueError:
                raise NameError("Invalid codepoint")
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["INT2CHAR"] = execute_INT2CHAR

        def execute_STRI2INT():
            """STRI2INT (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            [targ, val1, val2] = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            val1 = resolve_symb(val1, "string")
            val2 = resolve_symb(val2, "int")
            try:
                result = Value("int", ord(val1.content[val2.content]))
            except IndexError:
                raise NameError("Invalid index")
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["STRI2INT"] = execute_STRI2INT

        def execute_INT2FLOAT():
            """INT2FLOAT (var)targ (symb)val"""
            check_opcount(2)
            targ, val = instr.operands
            validate_operand(targ, "var")
            val = resolve_symb(val, "int")
            result = Value("float", float(val.content).hex())
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["INT2FLOAT"] = execute_INT2FLOAT

        def execute_FLOAT2INT():
            """FLOAT2INT (var)targ (symb)val"""
            check_opcount(2)
            targ, val = instr.operands
            validate_operand(targ, "var")
            val = resolve_symb(val, "float")
            result = Value("int", int(val.content))
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["FLOAT2INT"] = execute_FLOAT2INT

        def execute_READ():
            """READ (var)targ (type)ttype"""
            check_opcount(2)
            [targ, ttype] = instr.operands
            validate_operand(targ, "var")
            validate_operand(ttype, "type")
            value = Value(ttype.content, self.input_queue.dequeue())
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, value)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{value}\033[0m"
                )

        opcode_impl["READ"] = execute_READ

        def execute_WRITE():
            """WRITE (symb)val"""
            check_opcount(1)
            [val] = instr.operands
            validate_operand(val, "symb")
            val = resolve_symb(val)
            print(str(val), end="")
            if self._verbose:
                print("")

        opcode_impl["WRITE"] = execute_WRITE

        def execute_CONCAT():
            """CONCAT (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            [targ, val1, val2] = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            val1 = resolve_symb(val1, "string")
            val2 = resolve_symb(val2, "string")
            result = Value("string", val1.content + val2.content)
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["CONCAT"] = execute_CONCAT

        def execute_STRLEN():
            """STRLEN (var)targ (symb)val"""
            check_opcount(2)
            [targ, val] = instr.operands
            validate_operand(targ, "var")
            validate_operand(val, "symb")
            val = resolve_symb(val, "string")
            result = Value("int", len(val.content))
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["STRLEN"] = execute_STRLEN

        def execute_GETCHAR():
            """GETCHAR (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            [targ, val1, val2] = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            val1 = resolve_symb(val1, "string")
            val2 = resolve_symb(val2, "int")
            try:
                result = Value("string", val1.content[val2.content])
            except IndexError:
                raise NameError("Invalid index")
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["GETCHAR"] = execute_GETCHAR

        def execute_SETCHAR():
            """SETCHAR (var)targ (symb)val1 (symb)val2"""
            check_opcount(3)
            [targ, val1, val2] = instr.operands
            validate_operand(targ, "var")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            targ = resolve_symb(targ, "string")
            val1 = resolve_symb(val1, "int")
            val2 = resolve_symb(val2, "string")
            try:
                targ_list = list(targ.content)
                targ_list[val1.content] = val2.content[0]
                targ.content = "".join(targ_list)
            except IndexError:
                raise NameError("Invalid index")

        opcode_impl["SETCHAR"] = execute_SETCHAR

        def execute_TYPE():
            """TYPE (var)targ (symb)val"""
            check_opcount(2)
            [targ, val] = instr.operands
            validate_operand(targ, "var")
            validate_operand(val, "symb")
            try:
                val = resolve_symb(val)
                result = Value("string", val.type)
            except RuntimeError:
                val = Value("nil", None)
                result = Value("string", "")
            frame = self.get_frame(targ.frame)
            frame.set_variable(targ.name, result)
            if self._verbose:
                print(
                    f"    \033[32m{targ.frame}@\033[0m{targ.name} = \033[33m{result}\033[0m"
                )

        opcode_impl["TYPE"] = execute_TYPE

        def execute_LABEL():
            """LABEL (label)label"""
            check_opcount(1)
            # Náveštia rieši XML parser

        opcode_impl["LABEL"] = execute_LABEL

        def execute_JUMP():
            """JUMP (label)label"""
            check_opcount(1)
            [label] = instr.operands
            validate_operand(label, "label")
            if label.name not in self.labels:
                raise RuntimeError(f"Label {label.name} not found")
            self.program_counter = self.labels[label.name]

        opcode_impl["JUMP"] = execute_JUMP

        def execute_JUMPIFEQ():
            """JUMPIFEQ (label)label (symb)val1 (symb)val2"""
            check_opcount(3)
            [label, val1, val2] = instr.operands
            validate_operand(label, "label")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            val1 = resolve_symb(val1)
            val2 = resolve_symb(val2)
            if val1.type == val2.type and val1.content == val2.content:
                if label.name not in self.labels:
                    raise RuntimeError(f"Label {label.name} not found")
                self.program_counter = self.labels[label.name]

        opcode_impl["JUMPIFEQ"] = execute_JUMPIFEQ

        def execute_JUMPIFNEQ():
            """JUMPIFNEQ (label)label (symb)val1 (symb)val2"""
            check_opcount(3)
            [label, val1, val2] = instr.operands
            validate_operand(label, "label")
            validate_operand(val1, "symb")
            validate_operand(val2, "symb")
            val1 = resolve_symb(val1)
            val2 = resolve_symb(val2)
            if val1 != val2:
                if label.name not in self.labels:
                    raise RuntimeError(f"Label {label.name} not found")
                self.program_counter = self.labels[label.name]

        opcode_impl["JUMPIFNEQ"] = execute_JUMPIFNEQ

        def execute_EXIT():
            """EXIT (symb)val"""
            check_opcount(1)
            [val] = instr.operands
            validate_operand(val, "symb")
            val = resolve_symb(val, "int")
            if val.content < 0 or val.content > 49:
                raise ValueError("Invalid exit code")
            return val.content

        opcode_impl["EXIT"] = execute_EXIT

        def execute_DPRINT():
            """DPRINT (symb)val"""
            check_opcount(1)
            [val] = instr.operands
            validate_operand(val, "symb")
            val = resolve_symb(val)
            print(str(val), file=sys.stderr, end="")

        opcode_impl["DPRINT"] = execute_DPRINT

        def execute_BREAK():
            """BREAK"""
            check_opcount(0)
            print(repr(self), file=sys.stderr)

        opcode_impl["BREAK"] = execute_BREAK

        iexecute = opcode_impl.get(instr.opcode)
        if iexecute:
            retcode = iexecute()
        else:
            raise RuntimeError("Unrecognised instruction")

        self.program_counter += 1
        return retcode or 0
