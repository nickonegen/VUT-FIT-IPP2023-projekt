Implementačná dokumentácia k 1. úlohe do IPP 2022/2023 \
Meno a priezvisko: Onegen Something \
Login: xonege99

------------------------------------------------------

# parse.php - Analyzátor a prevodník IPPcode23 na XML #

## Spustenie ##

```bash
php8.1 parse.php [MOŽNOSTI] <zdroj xml>
```

Kompletný zoznam vstupných argumentov je obsiahnutý v nápovede, zobraziteľnou parametrom `--help`. Argumenty sú spracovávané "ručne", teda, po kontrole prítomnosti `--help`, cyklom rozpoznávajúci argumenty podľa konštanty `VALID_OPTS` a zapisujúci ich do globálneho poľa `$GINFO[statopt]`. Keďže jeden argument môže byť zadaní viac-krát a na jeho pozícií záleží, getopt() nebolo vhodné použiť.

## Analýza vstupného kódu ##

Metódy analýzy kódu sú definované v súbore `lib_parse/ippc_parser.php`.

Vstupný kód je analyzovaní riadok-po-riadku funkciou `ippc_parse_line()` ktorá je cyklicky volaná do ukončenia vstupného súboru. Pred spracovaním samotnej inštrukcie je kód zbavený komentárov, viac-násobných bielych znakov či prázdnych riadkov metódou `ippc_preparse()`, po čom prebiehajú globálne kontroly ako prítomnosť hlavičky `.IPPcode23` na prvom funkčnom riadku.
Všetky platné inštrukcie jazyka IPPcode23 sú definované v globálnom asociatívnom poli `INSTR`, ktoré obsahuje id inštrukcie a pole platných argumentov `argt`. Hodnoty v poli `argt` určujú typ očakávaného argumentu inštrukcie (podľa výčtu `OPERAND`). V metóde `ippc_parse_line()` sa pomocou `INSTR` overuje existencia inštrukcie, správny počet argumentov a napokon správny typ a formát argumentov - na čo slúžia najmä metódy `ippc_parse_var()` a `ippc_parse_const()`. V prípade akejkoľvek chyby je priebeh programu ukončený s chybovým hlásením na štandardnom chybovom výstupe (XML výstup či štatistiky sú zahodené).

## Tvorba XML reprezentácie kódu ##

Metódy tvorby XML reprezentácie sú definované v súbore `lib_parse/ippc_to_xml.php`.

Na tvorbu XML je používaná PHP knižnica [SimpleXML](https://www.php.net/manual/en/book.simplexml.php). Syntaktický analyzátor (metódy `ippc_parse_*`) po overení správnosti volá metódy vytvárajúce XML reprezentáciu každej inštrukcie, ktorá je pridaná ako potomok globálneho XML prvku `$XML`. `$XML` je inicializovaný pred začiatkom analýzy metódou `ippcXML_new_root()`, a v rámci analýzy sú doň pridávané inštrukcie pomocou `ippcXML_add_instruction()`, a argumenty pomocou `ippcXML_add_arg()` - argumenty sú definované pred ich analýzou a typ/hodnoty sú nastavované ďalšími metódami ako `ippcXML_make_variable()` alebo `ippcXML_make_constant()`. Na konci analýzy je XML reprezentácia vypísaná na štandardný výstup metódou `ippcXML_asXML()` ktorá XML súbor taktiež formátuje - formátovanie SimpleXML nepodporuje, takže reprezentácia je prevedená na DOMDocument (knižnica [DOM](https://www.php.net/manual/en/book.dom.php)), a až potom vypísaná.

## Štatistika (rozšírenie STATP) ##

Metódy spracovania dát a tvorby štatistiky sú definované v súbore `lib_parse/ippc_stats.php`.

Pokiaľ je program volaní s možnosťou `--stats`, budú ukladané dáta o vstupnom kóde podľa zadania. O každej inštrukcií je ukladaní počet použití (asociatívnym poľom `$GINFO[opstat]`) a každý skok či náveštie je "registrované" - program je jednopriechodový, takže sú vedené polia známych a neznámych náveští. Pokiaľ skok smeruje na známe náveštie, ide o spätný skok, v opačnom prípade je náveštie pridané do poľa neznámych náveští, ktoré sa buď neskôr nájde a ide o skok dopredu, alebo je skok neplatný. Inštrukcia `CALL` je považovaná za obyčajný skok, inštrukcia `RETURN` je počítaná ako skok, ale smer nie je určovaný. Počet riadkov s inštrukciami či počet komentárov je inkrementovaný počas funkcie `preparse` - tieto hodnoty sú ukladané nezávisle od `--stats`, počet inštrukcií je používaný aj pre kontrolu hlavičky. Po úspešnej analýze sú štatistiky podľa zadaných možností vypísané do súboru špecifikovaného možnosťou `--stats=FILE` metódou `ippcstat_collect()`.
