"""
Implementácia triedy interprétu IPPcode23.
@author: Onegen Something <xonege99@vutbr.cz>
"""

import xml.etree.ElementTree as ET
from lib_interpret.ippc_idata import Stack, UnresolvedVariable, Value
from lib_interpret.ippc_icontrol import Frame, Instruction


class Interpreter:
    """
    Trieda reprezentujúca celkový interpret jazyka IPPcode23.

    Atribúty:
        instructions (list): zoznam všetkých instrukcií
        program_counter (int): počítadlo spracovaných inštrukcií
        frames (dict): slovník dátových rámcov
        frame_stack (Stack): zásobník dátových rámcov (vrchol = LF)
        data_stack (Stack): zásobník dátových hodnôt
        labels (dict): slovník náveští
    """

    def __init__(self, xml_file):
        self.instructions = []
        self.program_counter = 0
        self.frames = {"global": Frame(), "temporary": None}
        self.frame_stack = Stack()
        self.data_stack = Stack()
        self.labels = {}
        self.parse_xml(xml_file)

    def __repr__(self):
        return "\n".join(f"{key}: {value}" for key, value in vars(self).items())

    def parse_xml(self, xml_file):
        """
        Načíta XML súbor IPPcode23 a získa z neho zoznam inštrukcií.

        Argumenty:
            xml_file (str): názov XML súboru

        Vyvolá:
            ET.ParseError: nesprávne XML formátovanie
        """
        temp_instructions = {}

        xml = ET.parse(xml_file)
        root = xml.getroot()

        # for instr_elm in root:
        # TODO: Implement

        # temp_instructions[order] = instruction

        for order in sorted(temp_instructions.keys()):
            self.instructions.append(temp_instructions[order])
