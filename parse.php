<?php

/**
 * IPP projekt 2023, časť 1
 * 
 * Lexikálny a syntaktický analyzátor, a prevodník
 * zdrojového kódu v IPPcode23 do XML reprezentácie.
 * @author Onegen Something <xonege99@vutbr.cz>
 * 
 * @param bool $help Vlajka '-help' na zobrazenie nápovedy
 */

ini_set("display_errors", "stderr");

/** @var \ArrayObject RETCODE Návratový kód */
define("RETCODE", array(
	"OK"		=> 0,
	"EPARAM"	=> 10,
	"ENOENT"	=> 11,	// Zbytočné? (používa sa iba stdin)
	"EWRITE"	=> 12,	// Zbytočné? (používa sa stdout, súbor iba s STATP)
	"ENOHEAD"	=> 21,
	"EOPCODE"	=> 22,
	"EANLYS"	=> 23,
	"EINT"	=> 99
));

/** @var \ArrayObject $opts Parametre spustenia */
$opts = getopt("", array(
	"help",
	// STATP?
));

/** @var \ArrayObject GINFO Objekt pre kontroly */
$GINFO = array(
	"header"	=> false,
	"stats"	=> false,
	"color"	=> true, // Farebný výstup
	"lines"	=> 0,
	"i_lines"	=> -1,
	"c_lines"	=> 0,
);

/** @var \ArrayObject OPERAND Výčet operandov */
define("OPERAND", array(
	"var"	=> 1,
	"symb"	=> 2,
	"label"	=> 3,
	"type"	=> 4
));

/** @var \ArrayObject INSTR Výčet/objekt inštrukcií */
define("INSTR", array(
	// Inštrukcie programových rámcov
	"MOVE" => array(
		"id"		=> 1,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"]
		)
	),
	"CREATEFRAME" => array(
		"id"		=> 2,
		"argt"	=> array()
	),
	"PUSHFRAME" => array(
		"id"		=> 3,
		"argt"	=> array()
	),
	"POPFRAME" => array(
		"id"		=> 4,
		"argt"	=> array()
	),
	"DEFVAR" => array(
		"id"		=> 5,
		"argt"	=> array(
			OPERAND["var"]
		)
	),
	"CALL" => array(
		"id"		=> 6,
		"argt"	=> array(
			OPERAND["label"]
		)
	),
	"RETURN" => array(
		"id"		=> 7,
		"argt"	=> array()
	),
	// Inštrukcie dátového zásobníka
	"PUSHS" => array(
		"id"		=> 8,
		"argt"	=> array(
			OPERAND["symb"]
		)
	),
	"POPS" => array(
		"id"		=> 9,
		"argt"	=> array(
			OPERAND["var"]
		)
	),
	// Aritmetické a dátové inštrukcie
	"ADD" => array(
		"id"		=> 10,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	"SUB" => array(
		"id"		=> 11,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	"MUL" => array(
		"id"		=> 12,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	"IDIV" => array(
		"id"		=> 13,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	"LT" => array(
		"id"		=> 14,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	"GT" => array(
		"id"		=> 15,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	"EQ" => array(
		"id"		=> 16,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	"AND" => array(
		"id"		=> 17,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	"OR" => array(
		"id"		=> 18,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	"NOT" => array(
		"id"		=> 19,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	"INT2CHAR" => array(
		"id"		=> 20,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"]
		)
	),
	"STRI2INT" => array(
		"id"		=> 21,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	// Vstupno-výstupné inštrukcie
	"READ" => array(
		"id"		=> 22,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["type"]
		)
	),
	"WRITE" => array(
		"id"		=> 23,
		"argt"	=> array(
			OPERAND["symb"]
		)
	),
	// Inštrukcie reťazcov
	"CONCAT" => array(
		"id"		=> 24,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	"STRLEN" => array(
		"id"		=> 25,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"]
		)
	),
	"GETCHAR" => array(
		"id"		=> 26,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	"SETCHAR" => array(
		"id"		=> 27,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	// Inštrukcie typu
	"TYPE" => array(
		"id"		=> 28,
		"argt"	=> array(
			OPERAND["var"],
			OPERAND["symb"]
		)
	),
	// Inštrukcie riadenia toku programu
	"LABEL" => array(
		"id"		=> 29,
		"argt"	=> array(
			OPERAND["label"]
		)
	),
	"JUMP" => array(
		"id"		=> 30,
		"argt"	=> array(
			OPERAND["label"]
		)
	),
	"JUMPIFEQ" => array(
		"id"		=> 31,
		"argt"	=> array(
			OPERAND["label"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	"JUMPIFNEQ" => array(
		"id"		=> 32,
		"argt"	=> array(
			OPERAND["label"],
			OPERAND["symb"],
			OPERAND["symb"]
		)
	),
	"EXIT" => array(
		"id"		=> 33,
		"argt"	=> array(
			OPERAND["symb"]
		)
	),
	// Inštrukcie na ladenie
	"DPRINT" => array(
		"id"		=> 34,
		"argt"	=> array(
			OPERAND["symb"]
		)
	),
	"BREAK" => array(
		"id"		=> 35,
		"argt"	=> array()
	),
));

/* Nápoveda */
if (isset($opts["help"])) {
	echo "Usage: php8.1 parse.php [OPTIONS]\n";
	echo "\n";
	echo "  --help              Print this help message\n";
	echo "\n";
	echo "Expects IPPcode23 code on standard input, which will be\n";
	echo "parsed and checked for syntax errors. If no errors are\n";
	echo "found, XML representation of the code is printed on\n";
	echo "standard output.\n";
	exit(RETCODE["OK"]);
}

/* Spracovanie vstupu */
for ($lineno = 0; $line = fgets(STDIN); $lineno++) {
	$GINFO["lines"] = $lineno + 1;

	// Celý riadok je komentár
	if (preg_match('/^\s*#.*/', $line)) {
		$GINFO["c_lines"]++;
		continue;
	}

	// Odstránenie komentárov
	if (preg_match('/^.*#/', $line)) $GINFO["c_lines"]++;
	$line = preg_replace('/#.*$/', '', $line);

	// Odstránenie nadbytočných bielych znakov
	$line = preg_replace('/\s+/', ' ', $line);
	$line = trim($line);

	// Prázdny riadok
	if (preg_match('/^\s*$/', $line)) continue;

	// Prvý neprázdny riadok musí byť hlavička
	if ($GINFO["i_lines"] < 0) {
		if (preg_match('/^\.IPPcode23$/', $line)) {
			$GINFO["header"] = true;
			$GINFO["i_lines"] = 0;
			continue;
		} else {
			throw_err(
				"ENOHEAD",
				$lineno,
				"Missing .IPPcode23 header"
			);
		}
	}

	// Spracovanie riadku
	$GINFO["i_lines"]++;
	parse_line($line);

	// DEBUG - spracovať iba jeden riadok
	// if ($GINFO["i_lines"] > 0) break;
}

if (!$GINFO["header"]) {
	throw_err(
		"ENOHEAD",
		$lineno,
		"Missing .IPPcode23 header (empty file)"
	);
}

function parse_line(string $line): void {
	global $GINFO;

	// Rozdelenie riadku na inštrukciu a argumenty
	$inst = explode(" ", $line);
	if (!isset($inst[0])) {
		throw_err(
			"EOPCODE",
			$GINFO["lines"],
			"Missing operation code"
		);
	}
	$inst[0] = strtoupper($inst[0]);

	// Kontrola, či je inštrukcia vo výčte
	if (!isset(INSTR[$inst[0]])) {
		throw_err(
			"EOPCODE",
			$GINFO["lines"],
			"Unknown instruction $inst[0]"
		);
	}
	$operation = INSTR[$inst[0]];

	// Kontrola počtu argumentov
	$inst_argc = count($inst) - 1;
	if ($inst_argc != count($operation["argt"])) {
		throw_err(
			"EANLYS",
			$GINFO["lines"],
			"$inst[0] expects "
				. count($operation["argt"])
				. " arguments, got $inst_argc"
		);
	}

	// Kontrola argumentov
	for ($i = 1; $i < count($inst); $i++) {
		$arg = $inst[$i];
		$arg_type = $operation["argt"][$i - 1];

		switch ($arg_type) {
			case OPERAND["var"]:
				if (!is_valid_var($arg)) {
					throw_err(
						"EANLYS",
						$GINFO["lines"],
						"Invalid variable $arg"
					);
				}
				break;
			case OPERAND["symb"]:
				if (!is_valid_var($arg) && !is_valid_const($arg)) {
					throw_err(
						"EANLYS",
						$GINFO["lines"],
						"Invalid symbol $arg"
					);
				}
				break;
			case OPERAND["label"]:
				if (!is_valid_id($arg)) {
					throw_err(
						"EANLYS",
						$GINFO["lines"],
						"Invalid label $arg"
					);
				}
				break;
			case OPERAND["type"]:
				if (!is_valid_type($arg)) {
					throw_err(
						"EANLYS",
						$GINFO["lines"],
						"Invalid type $arg"
					);
				}
				break;
			default:
				throw_err(
					"EANLYS",
					$GINFO["lines"],
					"Couldn't validate type of $arg"
				);
		}
	}

	echo implode(' ', $inst) . "\n"; // DEBUG
	return;
}

function is_valid_var(string $op): bool {
	// TODO
	return true;
}

function is_valid_const(string $op): bool {
	// TODO
	return true;
}

function is_valid_id(string $op): bool {
	// TODO
	return true;
}

function is_valid_type(string $op): bool {
	// TODO
	return true;
}

function throw_err(string $ecode, int $ln, string $msg): void {
	global $GINFO;

	$ERR = $GINFO["color"] ? "\033[31;49;1mERR!\033[0m" : "ERR!";
	$CODE = $GINFO["color"] ? "\033[35;49mcode\033[0m" : "code";
	$LINE = $GINFO["color"] ? "\033[35;49mline\033[0m" : "line";
	$err_string = "$ERR $CODE $ecode\n"
		. "$ERR $LINE $ln\n"
		. "$ERR $msg";

	error_log($err_string);
	exit(RETCODE[$ecode]);
}