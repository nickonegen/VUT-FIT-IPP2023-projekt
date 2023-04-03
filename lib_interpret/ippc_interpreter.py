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

    def __init__(self, xml):
        self.instructions = Queue()
        self.program_counter = 0
        self.frames = {"global": Frame(), "temporary": None}
        self.frame_stack = Stack()
        self.data_stack = Stack()
        self.input_queue = Queue()
        self.labels = {}
        self.parse_xml(xml)

    def __repr__(self):
        repr_str = f"#############################\n"
        repr_str += f"# START OF INTERPRETER DUMP #\n"
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
        return repr_str + f"# END OF INTERPRETER DUMP #\n###########################"

    def parse_xml(self, xml_str):
        def parse_operand(arg_elm):
            arg_type = arg_elm.attrib["type"]
            if arg_type in ["int", "string", "bool", "float", "type", "nil"]:
                return Value(arg_type, arg_elm.text)
            elif arg_type == "var":
                return UnresolvedVariable(arg_elm.text)
            elif arg_type == "label":
                return LabelArg(arg_elm.text)
            else:
                raise KeyError(f"Invalid argument type {arg_type}")

        temp_instructions = {}

        xml = ET.fromstring(xml_str)  # skipcq: BAN-B314
        if xml.tag != "program" or xml.attrib["language"] != "IPPcode23":
            raise KeyError("Invalid XML root element")

        for instr_elm in xml:
            if instr_elm.tag == "instruction":
                order = int(instr_elm.attrib["order"])
                opcode = instr_elm.attrib["opcode"]

                operands = []
                for arg_elm in instr_elm:
                    if arg_elm.tag in ["arg1", "arg2", "arg3"]:
                        arg_idx = int(arg_elm.tag[-1])
                        if arg_idx > 3 or arg_idx < 1 or arg_idx != len(operands) + 1:
                            raise KeyError(f"Invalid argument index {arg_idx}")

                        operands.append(parse_operand(arg_elm))

                temp_instructions[order] = Instruction(opcode, operands)

        for order in sorted(temp_instructions.keys()):
            self.instructions.enqueue(temp_instructions[order])
