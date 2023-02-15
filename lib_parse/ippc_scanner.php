<?php

/**
 * Pomocná knižnica pre lexikálnu analýzu IPPcode23
 * @author Onegen Something <xonege99@vutbr.cz>
 */

include 'ippc_to_xml.php';
include 'ippc_stats.php';

/** @var \ArrayObject DTYPE Výčet dátových typov */
define('DTYPE', [
	'int' => 0,
	'bool' => 1,
	'string' => 2,
	'nil' => 3,
]);

/** @var \ArrayObject OPERAND Výčet operandov */
define('OPERAND', [
	'var' => 1,
	'symb' => 2,
	'label' => 3,
	'type' => 4,
]);

/** @var \ArrayObject INSTR Výčet/objekt inštrukcií */
define('INSTR', [
	// Inštrukcie programových rámcov
	'MOVE' => [
		'id' => 1,
		'argt' => [OPERAND['var'], OPERAND['symb']],
	],
	'CREATEFRAME' => [
		'id' => 2,
		'argt' => [],
	],
	'PUSHFRAME' => [
		'id' => 3,
		'argt' => [],
	],
	'POPFRAME' => [
		'id' => 4,
		'argt' => [],
	],
	'DEFVAR' => [
		'id' => 5,
		'argt' => [OPERAND['var']],
	],
	'CALL' => [
		'id' => 6,
		'argt' => [OPERAND['label']],
	],
	'RETURN' => [
		'id' => 7,
		'argt' => [],
	],
	// Inštrukcie dátového zásobníka
	'PUSHS' => [
		'id' => 8,
		'argt' => [OPERAND['symb']],
	],
	'POPS' => [
		'id' => 9,
		'argt' => [OPERAND['var']],
	],
	// Aritmetické a dátové inštrukcie
	'ADD' => [
		'id' => 10,
		'argt' => [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'SUB' => [
		'id' => 11,
		'argt' => [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'MUL' => [
		'id' => 12,
		'argt' => [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'IDIV' => [
		'id' => 13,
		'argt' => [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'LT' => [
		'id' => 14,
		'argt' => [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'GT' => [
		'id' => 15,
		'argt' => [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'EQ' => [
		'id' => 16,
		'argt' => [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'AND' => [
		'id' => 17,
		'argt' => [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'OR' => [
		'id' => 18,
		'argt' => [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'NOT' => [
		'id' => 19,
		'argt' => [OPERAND['var'], OPERAND['symb']],
	],
	'INT2CHAR' => [
		'id' => 20,
		'argt' => [OPERAND['var'], OPERAND['symb']],
	],
	'STRI2INT' => [
		'id' => 21,
		'argt' => [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	// Vstupno-výstupné inštrukcie
	'READ' => [
		'id' => 22,
		'argt' => [OPERAND['var'], OPERAND['type']],
	],
	'WRITE' => [
		'id' => 23,
		'argt' => [OPERAND['symb']],
	],
	// Inštrukcie reťazcov
	'CONCAT' => [
		'id' => 24,
		'argt' => [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'STRLEN' => [
		'id' => 25,
		'argt' => [OPERAND['var'], OPERAND['symb']],
	],
	'GETCHAR' => [
		'id' => 26,
		'argt' => [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'SETCHAR' => [
		'id' => 27,
		'argt' => [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	// Inštrukcie typu
	'TYPE' => [
		'id' => 28,
		'argt' => [OPERAND['var'], OPERAND['symb']],
	],
	// Inštrukcie riadenia toku programu
	'LABEL' => [
		'id' => 29,
		'argt' => [OPERAND['label']],
	],
	'JUMP' => [
		'id' => 30,
		'argt' => [OPERAND['label']],
	],
	'JUMPIFEQ' => [
		'id' => 31,
		'argt' => [OPERAND['label'], OPERAND['symb'], OPERAND['symb']],
	],
	'JUMPIFNEQ' => [
		'id' => 32,
		'argt' => [OPERAND['label'], OPERAND['symb'], OPERAND['symb']],
	],
	'EXIT' => [
		'id' => 33,
		'argt' => [OPERAND['symb']],
	],
	// Inštrukcie na ladenie
	'DPRINT' => [
		'id' => 34,
		'argt' => [OPERAND['symb']],
	],
	'BREAK' => [
		'id' => 35,
		'argt' => [],
	],
]);

/**
 * Pomocná funkcia analyzátora odstraňujúca komentáre,
 * a určujúca, či riadok treba ďalej spracovávať.
 *
 * @param string $line Riadok na overenie
 *
 * @return string|null Upravený riadok alebo null (ak riadok je prázdny)
 */
function ippc_preparse(string $line): ?string {
	global $GINFO;

	// Celý riadok je komentár
	if (ippc_is_comment($line)) {
		$GINFO['c_lines']++;
		return null;
	}

	// Odstránenie komentárov
	if (ippc_has_comment($line)) {
		$GINFO['c_lines']++;
		$line = ippc_remove_comments($line);
	}

	// Odstránenie nadbytočných bielych znakov
	$line = trim(preg_replace('/\s+/', ' ', $line));

	// Prázdny riadok
	if (ippc_is_empty_line($line)) {
		return null;
	}

	$GINFO['i_lines']++;
	return $line;
}

function ippc_parse_line(string $line): void {
	global $GINFO;

	// Odstrániť komentáre, ignorovať prázdne riadky
	$line = ippc_preparse($line);
	if (!$line) {
		return;
	}

	// Prvý neprázdny riadok musí byť hlavička
	if (!$GINFO['header']) {
		$GINFO['header'] = ippc_is_header($line)
			? true
			: throw_err(
				'ENOHEAD',
				$GINFO['lines'],
				'Missing .IPPcode23 header',
			);
		return;
	}

	// Rozdelenie riadku na inštrukciu a argumenty
	$instr_args = explode(' ', $line);
	$instr = array_shift($instr_args);
	$instr = isset($instr)
		? strtoupper($instr)
		: throw_err('EOPCODE', $GINFO['lines'], 'Missing operation code');

	// Kontrola, či je inštrukcia vo výčte
	$instr_id =
		INSTR[$instr] ??
		throw_err('EOPCODE', $GINFO['lines'], "Unknown instruction $instr");

	// XML element inštrukcie
	$instr_xml = ippcXML_add_instruction($instr);

	// Kontrola počtu argumentov
	$instr_argc = count($instr_args);
	$instr_argc === count($instr_id['argt']) ||
		throw_err(
			'EANLYS',
			$GINFO['lines'],
			"$instr expects " .
				count($instr_id['argt']) .
				" arguments, got $instr_argc",
		);

	// Spracovanie argumentov
	for ($i = 0; $i < $instr_argc; $i++) {
		$arg = $instr_args[$i];
		$arg_type = $instr_id['argt'][$i];
		$arg_xml = ippcXML_add_arg($instr_xml, $i + 1);

		switch ($arg_type) {
			case OPERAND['var']:
				ippc_parse_var($arg, $arg_xml) ||
					throw_err(
						'EANLYS',
						$GINFO['lines'],
						"Invalid variable $arg",
					);
				break;
			case OPERAND['symb']:
				ippc_parse_var($arg, $arg_xml) ||
					ippc_parse_const($arg, $arg_xml) ||
					throw_err(
						'EANLYS',
						$GINFO['lines'],
						"Invalid symbol $arg",
					);
				break;
			case OPERAND['label']:
				ippc_is_identifier($arg) ||
					throw_err(
						'EANLYS',
						$GINFO['lines'],
						"Invalid label $arg",
					);
				ippcXML_make_label($arg_xml, $arg);
				break;
			case OPERAND['type']:
				ippc_is_type($arg) ||
					throw_err(
						'EANLYS',
						$GINFO['lines'],
						"Invalid type $arg",
					);
				ippcXML_make_type($arg_xml, $arg);
				break;
			default:
				throw_err(
					'EANLYS',
					$GINFO['lines'],
					"Couldn't validate type of $arg",
				);
		}
	}
	
	// Štatistiky
	ippcstat_reg_instruction($instr);
	switch ($instr_id) {
		// Nové náveštie
		case INSTR['LABEL']:
			ippcstat_reg_label($instr_args[0]);
			break;
		// Skok
		case INSTR['CALL']:
		case INSTR['JUMP']:
		case INSTR['JUMPIFEQ']:
		case INSTR['JUMPIFNEQ']:
			ippcstat_reg_jump($instr_args[0]);
			break;
		default: // žiadna ďalšia štatistika
	}
}

/**
 * Analýza IPPcode23 premennej, a pridanie
 * do XML reprezentácie (ak je platná).
 *
 * @param string $op Operand (premenná na analýzu)
 * @param SimpleXMLElement $arg_xml XML element argumentu
 *
 * @return bool true, ak je premenná platná
 */
function ippc_parse_var(string $op, SimpleXMLElement $arg_xml): bool {
	$op_split = explode('@', $op, 2);

	// Kontrola formátu: FRAME@ID
	if (count($op_split) != 2) {
		return false;
	}

	[$var_frame, $var_id] = $op_split;

	// Kontrola FRAME = GF|LF|TF
	if (!ippc_is_frame($var_frame)) {
		return false;
	}

	// Kontrola ID
	if (!ippc_is_identifier($var_id)) {
		return false;
	}

	// Validná premenná -> pridanie do XML
	ippcXML_make_variable($arg_xml, $op);
	return true;
}

/**
 * Analýza IPPcode23 konštanty, a pridanie
 * do XML reprezentácie (ak je validná).
 *
 * @param string $op Operand (konštanta na analýzu)
 * @param SimpleXMLElement $arg_xml XML element argumentu
 *
 * @return bool true, ak je konštanta platná
 */
function ippc_parse_const(string $op, SimpleXMLElement $arg_xml): bool {
	$op_split = explode('@', $op, 2);

	// Kontrola formátu: TYPE@VALUE
	if (count($op_split) != 2) {
		return false;
	}

	[$const_type, $const_val] = $op_split;

	// Kontrola TYPE
	if (!ippc_is_type($const_type)) {
		return false;
	}
	$const_typeid = DTYPE[$const_type];

	// Kontrola VALUE
	switch ($const_typeid) {
		case DTYPE['int']:
			if (!preg_match_all('/^[+-]?[0-9]+$/', $const_val)) {
				return false;
			}
			break;
		case DTYPE['bool']:
			if (!preg_match_all('/^(true|false)$/', $const_val)) {
				return false;
			}
			break;
		case DTYPE['string']:
			if (preg_match_all('/[\s#]|(\\\\(?!\d{3}))/', $const_val)) {
				return false;
			}
			break;
		case DTYPE['nil']:
			if ($const_val != 'nil') {
				return false;
			}
			break;
		default:
			return false;
	}

	// Validná konštanta -> pridanie do XML
	ippcXML_make_constant($arg_xml, $const_type, $const_val);
	return true;
}

/**
 * Kontrola, či je identifikátor platný.
 *
 * @param string $op Identifikátor na kontrolu
 *
 * @return bool true, ak je identifikátor platný
 */
function ippc_is_identifier(string $op): bool {
	return (bool) preg_match_all(
		'/^[$&%!a-zA-Z_\-\*\?][$&%!\w\-\*\?]*$/',
		$op,
	);
}

/**
 * Kontrola, či je daný operand rámec (GF, LF, TF).
 *
 * @param string $op Operand na kontrolu
 *
 * @return bool true, ak je rámec
 */
function ippc_is_frame(string $op): bool {
	return (bool) preg_match_all('/^(GF|LF|TF)$/', $op);
}

/**
 * Je daný riadok komentár? (začína #, neobsahuje
 * žiadnu inštrukciu)
 *
 * @param string $line Riadok kódu
 *
 * @return bool true, ak je riadok komentár
 */
function ippc_is_comment(string $line): bool {
	return (bool) preg_match_all('/^\s*#.*/', $line);
}

/**
 * Je daný riadok prázdny?
 *
 * @param string $line Riadok kódu
 *
 * @return bool true, ak je prázdny
 */
function ippc_is_empty_line(string $line): bool {
	return (bool) preg_match_all('/^\s*$/', $line);
}

/**
 * Obsahuje daný riadok komentár?
 *
 * @param string $line Riadok kódu
 *
 * @return bool true, ak obsahuje komentár
 */
function ippc_has_comment(string $line): bool {
	return (bool) preg_match_all('/^.*#/', $line);
}

/**
 * Odstráni komentár z daného riadku.
 *
 * @param string $line Riadok kódu
 *
 * @return string Riadok bez komentára
 */
function ippc_remove_comments(string $line): string {
	return substr($line, 0, strpos($line, '#'));
}

/**
 * Je daný riadok hlavička .IPPcode23?
 *
 * @param string $line Riadok kódu
 *
 * @return bool true, ak je riadok hlavička
 */
function ippc_is_header(string $line): bool {
	return (bool) preg_match_all('/^\.IPPcode23$/', $line);
}

/**
 * Kontrola, či je $op typ.
 *
 * @param string $op Operand na kontrolu
 *
 * @return bool true, ak je operand platný typ
 */
function ippc_is_type(string $op): bool {
	return array_key_exists($op, DTYPE);
}
