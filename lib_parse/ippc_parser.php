<?php

/**
 * Pomocná knižnica pre lexikálnu analýzu IPPcode23
 * @author Onegen Something <xonege99@vutbr.cz>
 */


include 'ippc_to_xml.php';
include 'ippc_stats.php';


/* Konštanty a výčty */


/** @var \ArrayObject DTYPE Výčet dátových typov */
define('DTYPE', [
	'int'	=> 0,
	'bool'	=> 1,
	'string'	=> 2,
	'nil'	=> 3,
	'float'	=> 4,
]);

/** @var \ArrayObject OPERAND Výčet operandov */
define('OPERAND', [
	'var'	=> 1,
	'symb'	=> 2,
	'label'	=> 3,
	'type'	=> 4,
]);

/** @var \ArrayObject INSTR Výčet/objekt inštrukcií */
define('INSTR', [
	// Inštrukcie programových rámcov
	'MOVE' => [
		'id'		=> 1,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb']],
	],
	'CREATEFRAME' => [
		'id'		=> 2,
		'ext'	=> false,
		'argt'	=> [],
	],
	'PUSHFRAME' => [
		'id'		=> 3,
		'ext'	=> false,
		'argt'	=> [],
	],
	'POPFRAME' => [
		'id'		=> 4,
		'ext'	=> false,
		'argt'	=> [],
	],
	'DEFVAR' => [
		'id'		=> 5,
		'ext'	=> false,
		'argt'	=> [OPERAND['var']],
	],
	'CALL' => [
		'id'		=> 6,
		'ext'	=> false,
		'argt'	=> [OPERAND['label']],
	],
	'RETURN' => [
		'id'		=> 7,
		'ext'	=> false,
		'argt'	=> [],
	],
	// Inštrukcie dátového zásobníka
	'PUSHS' => [
		'id'		=> 8,
		'ext'	=> false,
		'argt'	=> [OPERAND['symb']],
	],
	'POPS' => [
		'id'		=> 9,
		'ext'	=> false,
		'argt'	=> [OPERAND['var']],
	],
	// Aritmetické a dátové inštrukcie
	'ADD' => [
		'id'		=> 10,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'SUB' => [
		'id'		=> 11,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'MUL' => [
		'id'		=> 12,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'IDIV' => [
		'id'		=> 13,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'DIV' => [
		'id'		=> 14,
		'ext'	=> true,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'LT' => [
		'id'		=> 15,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'GT' => [
		'id'		=> 16,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'EQ' => [
		'id'		=> 17,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'AND' => [
		'id'		=> 18,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'OR' => [
		'id'		=> 19,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'NOT' => [
		'id'		=> 20,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb']],
	],
	'INT2CHAR' => [
		'id'		=> 21,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb']],
	],
	'STRI2INT' => [
		'id'		=> 22,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'INT2FLOAT' => [
		'id'		=> 23,
		'ext'	=> true,
		'argt'	=> [OPERAND['var'], OPERAND['symb']],
	],
	'FLOAT2INT' => [
		'id'		=> 24,
		'ext'	=> true,
		'argt'	=> [OPERAND['var'], OPERAND['symb']],
	],
	// Vstupno-výstupné inštrukcie
	'READ' => [
		'id'		=> 25,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['type']],
	],
	'WRITE' => [
		'id'		=> 26,
		'ext'	=> false,
		'argt'	=> [OPERAND['symb']],
	],
	// Inštrukcie reťazcov
	'CONCAT' => [
		'id'		=> 27,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'STRLEN' => [
		'id'		=> 28,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb']],
	],
	'GETCHAR' => [
		'id'		=> 29,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'SETCHAR' => [
		'id'		=> 30,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	// Inštrukcie typu
	'TYPE' => [
		'id'		=> 31,
		'ext'	=> false,
		'argt'	=> [OPERAND['var'], OPERAND['symb']],
	],
	// Inštrukcie riadenia toku programu
	'LABEL' => [
		'id'		=> 32,
		'ext'	=> false,
		'argt'	=> [OPERAND['label']],
	],
	'JUMP' => [
		'id'		=> 33,
		'ext'	=> false,
		'argt'	=> [OPERAND['label']],
	],
	'JUMPIFEQ' => [
		'id'		=> 34,
		'ext'	=> false,
		'argt'	=> [OPERAND['label'], OPERAND['symb'], OPERAND['symb']],
	],
	'JUMPIFNEQ' => [
		'id'		=> 35,
		'ext'	=> false,
		'argt'	=> [OPERAND['label'], OPERAND['symb'], OPERAND['symb']],
	],
	'EXIT' => [
		'id'		=> 36,
		'ext'	=> false,
		'argt'	=> [OPERAND['symb']],
	],
	// Inštrukcie na ladenie
	'DPRINT' => [
		'id'		=> 37,
		'ext'	=> false,
		'argt'	=> [OPERAND['symb']],
	],
	'BREAK' => [
		'id'		=> 38,
		'ext'	=> false,
		'argt'	=> [],
	],
]);


/* Funkcie */


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

	$GINFO['i_lines']++;

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
	if ($instr_id['ext'] && $GINFO['legacy']) {
		throw_err('EOPCODE', $GINFO['lines'], "Instruction $instr not allowed in legacy mode");
	}

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
		// Skok s náveštím
		case INSTR['CALL']:
		case INSTR['JUMP']:
		case INSTR['JUMPIFEQ']:
		case INSTR['JUMPIFNEQ']:
			ippcstat_reg_jump($instr_args[0]);
			break;
		// Skok bez náveštia
		case INSTR['RETURN']:
			ippcstat_reg_jump();
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
		case DTYPE['float']:
			if (!preg_match_all('/^[+-]?0x[0-9a-fA-F]+(\.[0-9a-fA-F]+)?p[+-]?[0-9]+$/', $const_val)) {
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


/* Pomocné funkcie */


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
	return (bool) preg_match('/^(?:\.IPPcode23|\.IFJcode22)$/', $line);
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
