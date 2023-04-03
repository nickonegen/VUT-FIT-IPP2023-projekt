"""
Implementácia triedy interprétu IPPcode23.
@author: Onegen Something <xonege99@vutbr.cz>
"""

import xml.etree.ElementTree as ET  # skipcq: BAN-B405
from lib_interpret.ippc_idata import Stack, Queue, Value
from lib_interpret.ippc_icontrol import Frame, Instruction, LabelArg, UnresolvedVariable


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

    def __init__(self, xml, input):
        self.instructions = Queue()
        self.program_counter = 0
        self.frames = {"global": Frame(), "temporary": None}
        self.frame_stack = Stack()
        self.data_stack = Stack()
        self.input_queue = Queue()
        self.labels = {}
        self.parse_xml(xml)

        for line in input.splitlines():
            self.input_queue.enqueue(line)

    def __repr__(self):
        repr_str = "#############################\n"
        repr_str += "# START OF INTERPRETER DUMP #\n"
        repr_str += f"  Program counter: {self.program_counter}\n"
        repr_str += (
            f"    All instructions: {self.program_counter + self.instructions.size()}\n"
        )
        repr_str += f"  Frame stack size: {self.frame_stack.size()}\n"
        repr_str += f"    TF exists: {self.frames['temporary'] is not None}\n"
        repr_str += f"  Data stack size: {self.data_stack.size()}\n"
        repr_str += f"  Input queue size: {self.input_queue.size()}\n\n"

        # Global frame
        repr_str += f"Global frame variables: ({self.frames['global'].size()})\n"
        repr_str += f"{self.frames['global']}\n"

        # Data stack
        repr_str += f"Data stack: ({self.data_stack.size()})\n"
        repr_str += f"{self.data_stack}\n"

        # Input queue
        repr_str += f"Input queue: ({self.input_queue.size()})\n"
        repr_str += f"{self.input_queue}\n"

        # Labels
        repr_str += f"Labels: ({len(self.labels)})\n"
        repr_str += "\n".join([f"    {k} = {v}" for k, v in self.labels.items()]) + "\n"

        # Instructions
        repr_str += f"Instruction queue: ({self.instructions.size()})\n"
        repr_str += f"{self.instructions}\n"

        # End
        return repr_str + "# END OF INTERPRETER DUMP #\n###########################"

    def parse_xml(self, xml_str):
        """
        Spracovanie XML reprezentácie programu.

        Vyvolá:
            ET.ParseError: chybný XML formát
            KeyError: chybný XML obsah
        """

        def parse_operand(arg_elm):
            arg_type = arg_elm.attrib["type"]
            if arg_type in ["int", "string", "bool", "float", "type", "nil"]:
                return Value(arg_type, arg_elm.text)
            if arg_type == "var":
                return UnresolvedVariable(arg_elm.text)
            if arg_type == "label":
                return LabelArg(arg_elm.text)
            raise KeyError(f"Invalid argument type {arg_type}")

        temp_instructions = {}

        xml = ET.fromstring(xml_str)  # skipcq: BAN-B314
        if xml.tag != "program" or xml.attrib["language"] != "IPPcode23":
            raise KeyError("Invalid XML root element")

        for instr_elm in xml:
            if instr_elm.tag == "instruction":
                order = int(instr_elm.attrib["order"])
                opcode = instr_elm.attrib["opcode"].upper()

                operands = []
                for arg_elm in instr_elm:
                    if arg_elm.tag in ["arg1", "arg2", "arg3"]:
                        arg_idx = int(arg_elm.tag[-1])
                        if arg_idx > 3 or arg_idx < 1 or arg_idx != len(operands) + 1:
                            raise KeyError(f"Invalid argument index {arg_idx}")

                        operands.append(parse_operand(arg_elm))

                    if opcode == "LABEL":
                        self.labels[operands[0].value] = order

                temp_instructions[order] = Instruction(opcode, operands)

        for order in sorted(temp_instructions.keys()):
            self.instructions.enqueue(temp_instructions[order])

    def peek_instruction(self):
        """
        Vráti inštrukciu na vrchu zoznamu.

        Vráti:
            Instruction: inštrukcia
        """
        return self.instructions.top()

    def execute_next(self):
        """
        Vkoná jednu inštrukciu.

        Vráti:
            int: návratová hodnota (-1 = žiadna)

        Vyvolá:
            RuntimeError: sémantická chyba (ESEM)
            AttributeError: chyba parametrov (EPARAM)
            TypeError: chyba typu (EOTYPE)
            KeyError: chyba prístupu do premennej (ENOVAR)
            MemoryError: chyba rámca (ENOFRM)
            ValueError: neplatná hodnota (EVALUE)
            IndexError: neznáma hodnota (ENOVAL)
            NameError: chyba reťazca (ESTR)
            NotImplementedError: neimplementovaná inštrukcia
            Exception: iná chyba (EINT)
        """
        if self.instructions.is_empty():
            return -1

        self.program_counter += 1
        instr = self.instructions.dequeue()
        instr_name = instr.opcode.upper()

        def validate_operand(operand, expected_type):
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
                frame = get_frame(symb.frame)
                return frame.get_variable(symb.name)
            raise RuntimeError(f"{symb} is not a valid symbol")

        def check_opcount(expected_count):
            if len(instr.operands) != expected_count:
                raise RuntimeError(
                    f"{instr_name} needs {expected_count} operands, got {len(instr.operands)}"
                )

        def get_frame(name):
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

        match instr.opcode:
            case "DEFVAR":
                check_opcount(1)
                [var] = instr.operands
                validate_operand(var, "var")
                frame = get_frame(var.frame)
                frame.define_variable(var.name)

            case "READ":
                check_opcount(2)
                [target, type] = instr.operands
                validate_operand(target, "var")
                validate_operand(type, "type")
                value = Value(type.value, self.input_queue.dequeue())
                frame = get_frame(target.frame)
                frame.set_variable(target.name, value)

            case "WRITE":
                check_opcount(1)
                [value] = instr.operands
                validate_operand(value, "symb")
                value = resolve_symb(value)
                print(str(value), end="")
