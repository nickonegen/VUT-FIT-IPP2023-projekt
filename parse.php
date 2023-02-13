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

ini_set('display_errors', 'stderr');

/** @var \ArrayObject RETCODE Návratový kód */
define('RETCODE', [
	'OK'		=> 0,
	'EPARAM'	=> 10,
	'ENOENT'	=> 11, // Zbytočné? (používa sa iba stdin)
	'EWRITE'	=> 12, // Zbytočné? (používa sa stdout, súbor iba s STATP)
	'ENOHEAD'	=> 21,
	'EOPCODE'	=> 22,
	'EANLYS'	=> 23,
	'EINT'	=> 99,
]);

/** @var \ArrayObject $opts Parametre spustenia */
$opts = getopt('', [
	'help',
	// STATP?
]);

/** @var \ArrayObject GINFO Objekt pre kontroly */
$GINFO = [
	'header'	=> false, // Prítomnosť hlavičky
	'stats'	=> false, // --stats (STATP neimplementované)
	'color'	=> true, // Farebný výstup
	'lines'	=> 0, // Počet riadkov vstupu
	'i_lines'	=> 0, // Počet riadkov s inštrukciami
	'c_lines'	=> 0, // Počet riadkov s komentárami
];

/** @var \ArrayObject DTYPE Výčet dátových typov */
define('DTYPE', [
	'int'	=> 0,
	'bool'	=> 1,
	'string'	=> 2,
	'nil'	=> 3,
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
		'argt'	=> [OPERAND['var'], OPERAND['symb']],
	],
	'CREATEFRAME' => [
		'id'		=> 2,
		'argt'	=> [],
	],
	'PUSHFRAME' => [
		'id'		=> 3,
		'argt'	=> [],
	],
	'POPFRAME' => [
		'id'		=> 4,
		'argt'	=> [],
	],
	'DEFVAR' => [
		'id'		=> 5,
		'argt'	=> [OPERAND['var']],
	],
	'CALL' => [
		'id'		=> 6,
		'argt'	=> [OPERAND['label']],
	],
	'RETURN' => [
		'id'		=> 7,
		'argt'	=> [],
	],
	// Inštrukcie dátového zásobníka
	'PUSHS' => [
		'id'		=> 8,
		'argt'	=> [OPERAND['symb']],
	],
	'POPS' => [
		'id'		=> 9,
		'argt'	=> [OPERAND['var']],
	],
	// Aritmetické a dátové inštrukcie
	'ADD' => [
		'id'		=> 10,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'SUB' => [
		'id'		=> 11,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'MUL' => [
		'id'		=> 12,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'IDIV' => [
		'id'		=> 13,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'LT' => [
		'id'		=> 14,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'GT' => [
		'id'		=> 15,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'EQ' => [
		'id'		=> 16,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'AND' => [
		'id'		=> 17,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'OR' => [
		'id'		=> 18,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'NOT' => [
		'id'		=> 19,
		'argt'	=> [OPERAND['var'], OPERAND['symb']],
	],
	'INT2CHAR' => [
		'id'		=> 20,
		'argt'	=> [OPERAND['var'], OPERAND['symb']],
	],
	'STRI2INT' => [
		'id'		=> 21,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	// Vstupno-výstupné inštrukcie
	'READ' => [
		'id'		=> 22,
		'argt'	=> [OPERAND['var'], OPERAND['type']],
	],
	'WRITE' => [
		'id'		=> 23,
		'argt'	=> [OPERAND['symb']],
	],
	// Inštrukcie reťazcov
	'CONCAT' => [
		'id'		=> 24,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'STRLEN' => [
		'id'		=> 25,
		'argt'	=> [OPERAND['var'], OPERAND['symb']],
	],
	'GETCHAR' => [
		'id'		=> 26,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	'SETCHAR' => [
		'id'		=> 27,
		'argt'	=> [OPERAND['var'], OPERAND['symb'], OPERAND['symb']],
	],
	// Inštrukcie typu
	'TYPE' => [
		'id'		=> 28,
		'argt'	=> [OPERAND['var'], OPERAND['symb']],
	],
	// Inštrukcie riadenia toku programu
	'LABEL' => [
		'id'		=> 29,
		'argt'	=> [OPERAND['label']],
	],
	'JUMP' => [
		'id'		=> 30,
		'argt'	=> [OPERAND['label']],
	],
	'JUMPIFEQ' => [
		'id'		=> 31,
		'argt'	=> [OPERAND['label'], OPERAND['symb'], OPERAND['symb']],
	],
	'JUMPIFNEQ' => [
		'id'		=> 32,
		'argt'	=> [OPERAND['label'], OPERAND['symb'], OPERAND['symb']],
	],
	'EXIT' => [
		'id'		=> 33,
		'argt'	=> [OPERAND['symb']],
	],
	// Inštrukcie na ladenie
	'DPRINT' => [
		'id'		=> 34,
		'argt'	=> [OPERAND['symb']],
	],
	'BREAK' => [
		'id'		=> 35,
		'argt'	=> [],
	],
]);

/* Nápoveda */
if (isset($opts['help'])) {
	echo "Usage: php8.1 parse.php [OPTIONS]\n";
	echo "\n";
	echo "  --help              Print this help message\n";
	echo "\n";
	echo "Expects IPPcode23 code on standard input, which will be\n";
	echo "parsed and checked for syntax errors. If no errors are\n";
	echo "found, XML representation of the code is printed on\n";
	echo "standard output.\n";
	exit(RETCODE['OK']);
}

/* Spracovanie vstupu */
for ($lineno = 0; ($line = fgets(STDIN)); $lineno++) {
	$GINFO['lines'] = $lineno + 1;

	// Celý riadok je komentár
	if (is_comment($line)) {
		$GINFO['c_lines']++;
		continue;
	}

	// Odstránenie komentárov
	if (has_comment($line)) {
		$GINFO['c_lines']++;
		$line = remove_comments($line);
	}

	// Odstránenie nadbytočných bielych znakov
	$line = trim(preg_replace('/\s+/', ' ', $line));

	// Prázdny riadok
	if (is_empty_line($line)) {
		continue;
	}

	// Prvý neprázdny riadok musí byť hlavička
	if (!$GINFO['header']) {
		$GINFO['header'] = is_header($line)
			? true
			: throw_err('ENOHEAD', $lineno, 'Missing .IPPcode23 header');
		continue;
	}

	// Spracovanie riadku
	$GINFO['i_lines']++;
	parse_line($line);
}

$GINFO['header'] ||
	throw_err('ENOHEAD', $lineno, 'Missing .IPPcode23 header (empty file)');

function parse_line(string $line): void {
	global $GINFO;

	// Rozdelenie riadku na inštrukciu a argumenty
	$inst = explode(' ', $line);
	$inst[0] = !isset($inst[0])
		? throw_err('EOPCODE', $GINFO['lines'], 'Missing operation code')
		: strtoupper($inst[0]);

	// Kontrola, či je inštrukcia vo výčte
	$inst_code =
		INSTR[$inst[0]] ??
		throw_err('EOPCODE', $GINFO['lines'], "Unknown instruction $inst[0]");
	$inst_argc = count($inst) - 1;

	// Kontrola počtu argumentov
	$inst_argc === count($inst_code['argt']) ||
		throw_err(
			'EANLYS',
			$GINFO['lines'],
			"$inst[0] expects " .
				count($inst_code['argt']) .
				" arguments, got $inst_argc",
		);

	// Kontrola argumentov
	for ($i = 1; $i <= $inst_argc; $i++) {
		$arg = $inst[$i];
		$arg_type = $inst_code['argt'][$i - 1];

		switch ($arg_type) {
			case OPERAND['var']:
				is_valid_var($arg) ||
					throw_err(
						'EANLYS',
						$GINFO['lines'],
						"Invalid variable $arg",
					);
				break;
			case OPERAND['symb']:
				is_valid_var($arg) ||
					is_valid_const($arg) ||
					throw_err(
						'EANLYS',
						$GINFO['lines'],
						"Invalid symbol $arg",
					);
				break;
			case OPERAND['label']:
				is_valid_id($arg) ||
					throw_err(
						'EANLYS',
						$GINFO['lines'],
						"Invalid label $arg",
					);
				break;
			case OPERAND['type']:
				is_valid_type($arg) ||
					throw_err(
						'EANLYS',
						$GINFO['lines'],
						"Invalid type $arg",
					);
				break;
			default:
				throw_err(
					'EANLYS',
					$GINFO['lines'],
					"Couldn't validate type of $arg",
				);
		}
	}
}

function is_valid_var(string $op): bool {
	$op_split = explode('@', $op, 2);

	// Kontrola formátu: FRAME@ID
	if (count($op_split) != 2) {
		return false;
	}

	// Kontrola FRAME = GF|LF|TF
	if (!preg_match('/^(GF|LF|TF)$/', $op_split[0])) {
		return false;
	}

	// Kontrola ID
	if (!is_valid_id($op_split[1])) {
		return false;
	}

	return true;
}

function is_valid_const(string $op): bool {
	$op_split = explode('@', $op, 2);

	// Kontrola formátu: TYPE@VALUE
	if (count($op_split) != 2) {
		return false;
	}

	// Kontrola TYPE
	if (!is_valid_type($op_split[0])) {
		return false;
	}
	$op_type = DTYPE[$op_split[0]];

	// Kontrola VALUE
	switch ($op_type) {
		case DTYPE['int']:
			return (bool) preg_match_all('/^[+-]?[0-9]+$/', $op_split[1]);
			break;
		case DTYPE['bool']:
			return (bool) preg_match_all('/^(true|false)$/', $op_split[1]);
			break;
		case DTYPE['string']:
			return is_valid_string($op_split[1]);
			break;
		case DTYPE['nil']:
			return $op_split[1] == 'nil';
			break;
		default:
			return false;
	}
}

function is_valid_string(string $str): bool {
	return (bool) !preg_match_all('/[\s#]|(\\\\(?!\d{3}))/', $str);
}

function is_valid_id(string $op): bool {
	return (bool) preg_match_all(
		'/^[$&%!a-zA-Z_\-\*\?][$&%!\w\-\*\?]*$/',
		$op,
	);
}

function is_valid_type(string $op): bool {
	return array_key_exists($op, DTYPE);
}

function is_comment(string $line): bool {
	return (bool) preg_match_all('/^\s*#.*/', $line);
}

function has_comment(string $line): bool {
	return (bool) preg_match_all('/^.*#/', $line);
}

function remove_comments(string $line): string {
	return substr($line, 0, strpos($line, '#'));
}

function is_empty_line(string $line): bool {
	return (bool) preg_match_all('/^\s*$/', $line);
}

function is_header(string $line): bool {
	return (bool) preg_match_all('/^\.IPPcode23$/', $line);
}

function throw_err(string $ecode, int $ln, string $msg): void {
	global $GINFO;

	$color = $GINFO['color'];
	$ERR = $color ? "\033[31;49;1mERR!\033[0m" : 'ERR!';
	$CODE = $color ? "\033[35;49mcode\033[0m" : 'code';
	$LINE = $color ? "\033[35;49mline\033[0m" : 'line';
	$err_string = "$ERR $CODE $ecode\n" . "$ERR $LINE $ln\n" . "$ERR $msg";

	error_log($err_string);
	exit(RETCODE[$ecode]);
}
