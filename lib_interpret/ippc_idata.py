"""
Pomocné triedy a konštanty pre interpret.py
@author: Onegen Something <xonege99@vutbr.cz>
"""

RETCODE = {
    "OK": 0,
    "EPARAM": 10,  # Chybné parametre
    "ENOENT": 11,  # Chyba pri otváraní súboru
    "EWRITE": 12,  # Chyba pri zápise
    "EINT": 99,  # Interná chyba
    "EXML": 31,  # Chyba XML formátovania
    "ESTRUC": 32,  # Chybná štruktúra XML
    "ESEM": 52,  # Semantická chyba
    "EOTYPE": 53,  # Nepovolený typ operandu
    "ENOVAR": 54,  # Prístup k neexistujúcej premennej
    "ENOFRM": 55,  # Prístup k neexistujúcemu rámcu
    "ENOVAL": 56,  # Chýbajúca hodnota
    "EVALUE": 57,  # Chybná hodnota
    "ESTR": 58,  # Nesprávne zaobchádzanie s reťazcom
}

IEXCEPTIONC = {
    RuntimeError: "ESEM",
    TypeError: "EOTYPE",
    KeyError: "ENOVAR",
    MemoryError: "ENOFRM",
    ValueError: "EVALUE",
    IndexError: "ENOVAL",
    NameError: "ESTR",
}


class Stack:
    """Zásobník (pre rámce a hodnoty)"""

    def __init__(self):
        self._items = []

    def __repr__(self):
        if self.is_empty():
            return "  > (empty)\n"
        return (
            "  >  " + "\n     ".join(str(item) for item in reversed(self._items)) + "\n"
        )

    def is_empty(self):
        """Dotaz na prázdnosť zásobníka"""
        return len(self._items) == 0

    def push(self, item):
        """Pridá položku na vrchol zásobníka"""
        self._items.append(item)

    def pop(self):
        """Odoberie a vráti položku z vrcholu zásobníka (prádzny -> EINT)"""
        if not self.is_empty():
            return self._items.pop()
        raise Exception("Cannot access empty stack")

    def top(self):
        """Vráti položku na vrchole zásobníka (prázdny -> None)"""
        if not self.is_empty():
            return self._items[-1]
        return None

    def size(self):
        """Vráti počet položiek v zásobníku"""
        return len(self._items)


class Queue:
    """Fronta (pre vstup)"""

    def __init__(self):
        self._items = []

    def __repr__(self):
        if self.is_empty():
            return "  > (empty)\n"
        return "  >  " + "\n     ".join(str(item) for item in self._items) + "\n"

    def is_empty(self):
        """Dotaz na prázdnosť fronty"""
        return len(self._items) == 0

    def enqueue(self, item):
        """Pridá položku na koniec fronty"""
        self._items.append(item)

    def dequeue(self):
        """Odoberie a vráti položku zo začiatku fronty (prázdny -> EINT)"""
        if not self.is_empty():
            return self._items.pop(0)
        raise Exception("Cannot access empty queue")

    def top(self):
        """Vráti položku na začiatku fronty (prázdny -> None)"""
        if not self.is_empty():
            return self._items[0]
        return None

    def size(self):
        """Vráti počet položiek v fronte."""
        return len(self._items)
