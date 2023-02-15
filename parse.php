<?php

/**
 * IPP projekt 2023, časť 1
 *
 * Lexikálny a syntaktický analyzátor, a prevodník
 * zdrojového kódu v IPPcode23 do XML reprezentácie.
 * @author Onegen Something <xonege99@vutbr.cz>
 */

ini_set('display_errors', 'stderr');

/** @var \ArrayObject RETCODE Návratový kód */
define('RETCODE', [
	'OK'		=> 0,
	'EPARAM'	=> 10,
	'ENOENT'	=> 11,
	'EWRITE'	=> 12,
	'ENOHEAD'	=> 21,
	'EOPCODE'	=> 22,
	'EANLYS'	=> 23,
	'EINT'	=> 99,
]);

/** @var \ArrayObject VALIDOPTS Zoznam rozpoznávaných parametrov */
define('VALIDOPTS', [
	'help'		=> 'no',
	'stats'		=> 'req',
	'loc'		=> 'no',
	'comments'	=> 'no',
	'labels'		=> 'no',
	'jumps'		=> 'no',
	'fwjumps'		=> 'no',
	'backjumps'	=> 'no',
	'badjumps'	=> 'no',
	'frequent'	=> 'no',
	'print'		=> 'req',
	'eol'		=> 'no',
]);

/** @var \ArrayObject GINFO Globálny objekt pre kontroly a štatistiky */
$GINFO = [
	'header'	=> false,	// Prítomnosť hlavičky
	'fancy'	=> false,	// Farebný výstup
	'start'	=> microtime(true), // Čas spustenia
	'stats'	=> false,	// Vlajka výpisu štatistík
	'statsf'	=> '',	// Súbor pre výpis štatistík
	'statord'	=> [],	// Poradie výpisu štatistík
	'lines'	=> 0,	// Počet riadkov vstupu
	'i_lines'	=> 0,	// Počet riadkov s inštrukciami (--loc)
	'c_lines'	=> 0,	// Počet riadkov s komentárami (--comments)
	'opstat'	=> [],	// Štatistika inštrukcií
	'labels'	=> [
		'def'	=> [],	// Zoznam definovaných náveští
		'ndef'	=> [],	// Zoznam použitých, zatiaľ nedefinovaných náveští
	],
	'jumps'	=> [
		'fw'		=> 0,	// Počet skokov dopredu
		'bw'		=> 0,	// Počet skokov dozadu
	]
];

/** @var int FANCYSTATWIDTH Šírka textového "fancy" výstupu štatistík */
define('FANCYSTATWIDTH', 70);

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
if (array_search('--help', $argv)) {
	echo "Usage: php8.1 parse.php [OPTIONS] <source xml>\n";
	echo "\n";
	echo " Parses IPPcode23 code from standard input, and outputs\n";
	echo " XML representation of the code to standard output if\n";
	echo " no syntax or lexical errors are found.\n";
	echo "\n";
	echo "  --help              Print this help message and exit.\n";
	echo "  --stats=FILE        Write statistics to the given file.\n";
	echo "\n";
	echo " \033[1mStats Options\033[0m \033[3m(appends to --stats=FILE)\033[0m\n";
	echo "  --loc               Count of lines with instructions.\n";
	echo "  --comments          Count of lines with comments.\n";
	echo "  --labels            Count of defined labels.\n";
	echo "  --jumps             Count of all jumps.\n";
	echo "  --fwjumps           Count of forward jumps.\n";
	echo "  --backjumps         Count of backward jumps.\n";
	echo "  --badjumps          Count of jumps to undefined labels.\n";
	echo "  --frequent          List of most frequent instructions.\n";
	echo "  --print=STRING      Append STRING.\n";
	echo "  --eol               Append an empty line.\n";
	exit(RETCODE['OK']);
}

/* Spracovanie parametrov */
array_shift($argv);
foreach ($argv as $arg) {
	$arg = preg_replace('/^--?/', '', $arg);
	[$opt, $val] = explode('=', $arg, 2) + [1 => null];

	// Neznámy parameter
	if (!in_array($opt, array_keys(VALIDOPTS))) {
		continue;
	}

	if (VALIDOPTS[$opt] == 'req' && !$val) {
		// Parameter s povinnou hodnotou bez hodnoty
		throw_err('EPARAM', null, "Missing value for option --$opt");
	} elseif (VALIDOPTS[$opt] == 'no' && $val) {
		// Parameter bez hodnoty s hodnotou
		throw_err('EPARAM', null, "Option --$opt doesn't take a value");
	}

	// Všetky parametre mimo --help sú štatistické => --stats musí byť prvý
	if ($opt == 'stats') {
		// --stats nemôže byť 2x
		if ($GINFO['stats']) {
			throw_err(
				'EPARAM',
				null,
				"--stats option can't be used multiple times",
			);
		}

		$GINFO['stats'] = true;
		$GINFO['statf'] = $val;
		continue;
	} elseif (!$GINFO['stats']) {
		// Použitie štatistického parametra bez --stats
		throw_err(
			'EPARAM',
			null,
			"Option --$opt can't be used without preceding --stats",
		);
	}

	array_push($GINFO['statord'], [$opt, $val]);
}

/* Vytvorenie XML reprezentácie kódu */
$XML = new SimpleXMLElement(
	'<?xml version="1.0" encoding="UTF-8"?><program language="IPPcode23"></program>',
);

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

/* Výpis štatistík */
if ($GINFO['stats']) {
	$fancy = $GINFO['fancy'];
	$stat_file = fopen($GINFO['statf'], 'w');
	if (!$stat_file) {
		throw_err('EWRITE', null, "Can't open file {$GINFO['statf']}");
	}

	// Výpis štatistík
	$stat_string = '';
	$total = count($GINFO['statord']);
	$i = 0;
	foreach ($GINFO['statord'] as [$opt, $val]) {
		$stat_string .= print_stat($opt, $val);
		$i++;
		if ($i < $total) {
			$stat_string .= "\n";
		}
	}

	$stat_string = $fancy
		? 'parse.php for IPPcode23 by xonege99  ' .
			sprintf(
				'T=%.2f ms ',
				(microtime(true) - $GINFO['start']) * 1000,
			) .
			"({$GINFO['lines']} lines processed)\n" .
			str_repeat('-', 70) .
			"\n" .
			$stat_string .
			"\n" .
			str_repeat('-', 70)
		: $stat_string;
	fwrite($stat_file, $stat_string);
	fclose($stat_file);
}

/* Výpis XML reprezentácie kódu */
echo $XML->asXML();
//print_r($GINFO); // DEBUG
exit(RETCODE['OK']);

/* Funkcie */

/**
 * Analýza jedného riadku vstupného kódu,
 * a spracovanie do XML reprezentácie.
 *
 * @param string $line Riadok IPPcode23
 *
 * @return void
 */
function parse_line(string $line): void {
	global $GINFO;
	global $XML;

	// XML element inštrukcie
	$inst_xml = $XML->addChild('instruction');
	$inst_xml->addAttribute('order', $GINFO['i_lines']);

	// Rozdelenie riadku na inštrukciu a argumenty
	$inst = explode(' ', $line);
	$inst[0] = !isset($inst[0])
		? throw_err('EOPCODE', $GINFO['lines'], 'Missing operation code')
		: strtoupper($inst[0]);

	// Kontrola, či je inštrukcia vo výčte
	$inst_code =
		INSTR[$inst[0]] ??
		throw_err('EOPCODE', $GINFO['lines'], "Unknown instruction $inst[0]");
	$inst_xml->addAttribute('opcode', $inst[0]);

	// Kontrola počtu argumentov
	$inst_argc = count($inst) - 1;
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
		$arg_xml = $inst_xml->addChild('arg' . $i);

		switch ($arg_type) {
			case OPERAND['var']:
				parse_var($arg, $arg_xml) ||
					throw_err(
						'EANLYS',
						$GINFO['lines'],
						"Invalid variable $arg",
					);
				break;
			case OPERAND['symb']:
				parse_var($arg, $arg_xml) ||
					parse_const($arg, $arg_xml) ||
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
				$arg_xml->addAttribute('type', 'label');
				$arg_xml[0] = $arg;
				break;
			case OPERAND['type']:
				is_valid_type($arg) ||
					throw_err(
						'EANLYS',
						$GINFO['lines'],
						"Invalid type $arg",
					);
				$arg_xml->addAttribute('type', 'type');
				$arg_xml[0] = $arg;
				break;
			default:
				throw_err(
					'EANLYS',
					$GINFO['lines'],
					"Couldn't validate type of $arg",
				);
		}
	}

	// Pridanie inštrukcie do zoznamu (pre štatistiky)
	register_instruction($inst[0]);

	// Pridanie náveští a skokov do zoznamu
	switch ($inst_code) {
		// Nové náveštie
		case INSTR['LABEL']:
			register_label($inst[1]);
			break;
		// Skok
		case INSTR['CALL']:
		case INSTR['JUMP']:
		case INSTR['JUMPIFEQ']:
		case INSTR['JUMPIFNEQ']:
			register_jump($inst[1]);
			break;
		default:
		// no action
	}
}

/**
 * Analýza IPPcode23 premennej, a pridanie
 * do XML reprezentácie (ak je validná).
 *
 * @param string $op Operand (premenná na analýzu)
 * @param SimpleXMLElement $arg_xml XML element argumentu
 *
 * @return bool true, ak je premenná validná
 */
function parse_var(string $op, SimpleXMLElement $arg_xml): bool {
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

	// Validná premenná -> pridanie do XML
	$arg_xml->addAttribute('type', 'var');
	$arg_xml[0] = $op;
	return true;
}

/**
 * Analýza IPPcode23 konštanty, a pridanie
 * do XML reprezentácie (ak je validná).
 *
 * @param string $op Operand (konštantná hodnota na analýzu)
 * @param SimpleXMLElement $arg_xml XML element argumentu
 *
 * @return bool true, ak je konštantná hodnota validná
 */
function parse_const(string $op, SimpleXMLElement $arg_xml): bool {
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
			if (!preg_match_all('/^[+-]?[0-9]+$/', $op_split[1])) {
				return false;
			}
			break;
		case DTYPE['bool']:
			if (!preg_match_all('/^(true|false)$/', $op_split[1])) {
				return false;
			}
			break;
		case DTYPE['string']:
			if (!is_valid_string($op_split[1])) {
				return false;
			}
			break;
		case DTYPE['nil']:
			if ($op_split[1] != 'nil') {
				return false;
			}
			break;
		default:
			return false;
	}

	// Validná konštanta -> pridanie do XML
	$arg_xml->addAttribute('type', strtolower($op_split[0]));
	$arg_xml[0] = $op_split[1];
	return true;
}

/**
 * Kontrola, či je reťazec validný.
 *
 * @param string $str Reťazec na kontrolu
 *
 * @return bool true, ak je reťazec validný
 */
function is_valid_string(string $str): bool {
	return (bool) !preg_match_all('/[\s#]|(\\\\(?!\d{3}))/', $str);
}

/**
 * Kontrola, či je identifikátor validné.
 *
 * @param string $op Identifikátor na kontrolu
 *
 * @return bool true, ak je identifikátor validný
 */
function is_valid_id(string $op): bool {
	return (bool) preg_match_all(
		'/^[$&%!a-zA-Z_\-\*\?][$&%!\w\-\*\?]*$/',
		$op,
	);
}

/**
 * Kontrola, či je typ validný.
 *
 * @param string $op Typ na kontrolu
 *
 * @return bool true, ak je typ validný
 */
function is_valid_type(string $op): bool {
	return array_key_exists($op, DTYPE);
}

/**
 * Je daný riadok komentár? (začína #, neobsahuje
 * žiadnu inštrukciu)
 *
 * @param string $line Riadok kódu
 *
 * @return bool true, ak je riadok komentár
 */
function is_comment(string $line): bool {
	return (bool) preg_match_all('/^\s*#.*/', $line);
}

/**
 * Obsahuje daný riadok komentár?
 *
 * @param string $line Riadok kódu
 *
 * @return bool true, ak obsahuje komentár
 */
function has_comment(string $line): bool {
	return (bool) preg_match_all('/^.*#/', $line);
}

/**
 * Odstráni komentár z daného riadku.
 *
 * @param string $line Riadok kódu
 *
 * @return string Riadok bez komentára
 */
function remove_comments(string $line): string {
	return substr($line, 0, strpos($line, '#'));
}

/**
 * Je daný riadok prázdny?
 *
 * @param string $line Riadok kódu
 *
 * @return bool true, ak je prázdny
 */
function is_empty_line(string $line): bool {
	return (bool) preg_match_all('/^\s*$/', $line);
}

/**
 * Je daný riadok hlavička '.IPPcode23'?
 *
 * @param string $line Riadok kódu
 *
 * @return bool true, ak je hlavička
 */
function is_header(string $line): bool {
	return (bool) preg_match_all('/^\.IPPcode23$/', $line);
}

/**
 * Získanie jednej štatistiky.
 *
 * @param string $stat_name Názov štatistiky (parameter)
 * @param string|null $stat_optval Hodnota parametra (pre --print)
 *
 * @return string Riadok štatistiky
 */
function print_stat(string $stat_name, ?string $stat_optval): string {
	global $GINFO;

	$fancy = $GINFO['fancy'];
	$stat_title = '';
	$stat_string = '';

	switch ($stat_name) {
		case 'loc':
			$stat_title = 'Lines with instructions';
			$stat_string .= $GINFO['i_lines'];
			break;
		case 'comments':
			$stat_title = 'Lines with comments';
			$stat_string .= $GINFO['c_lines'];
			break;
		case 'labels':
			$stat_title = 'Labels';
			$stat_string .= count($GINFO['labels']['def']);
			break;
		case 'jumps':
			$stat_title = 'Total jumps';
			$stat_string .=
				$GINFO['jumps']['fw'] +
				$GINFO['jumps']['bw'] +
				count($GINFO['labels']['ndef']);
			break;
		case 'fwjumps':
			$stat_title = 'Forward jumps';
			$stat_string .= $GINFO['jumps']['fw'];
			break;
		case 'backjumps':
			$stat_title = 'Backward jumps';
			$stat_string .= $GINFO['jumps']['bw'];
			break;
		case 'badjumps':
			$stat_title = 'Bad jumps';
			$stat_string .= count($GINFO['labels']['ndef']);
			break;
		case 'frequent':
			$stat_title = 'Most frequent instructions';
			if (empty($GINFO['opstat'])) {
				break;
			}

			$max_op_use = max(array_values($GINFO['opstat']));
			$stat_string .= implode(
				',',
				array_keys($GINFO['opstat'], $max_op_use),
			);
			$stat_string .= $fancy ? " {$max_op_use}" : '';
			break;
		case 'print':
			$stat_string .= $stat_optval;
			break;
		case 'eol':
			$stat_string .= '';
			break;
		default:
			throw_err(
				'EPARAM',
				null,
				"Error in parsing statistic $stat_name",
			);
	}

	return $fancy
		? $stat_title .
				str_repeat(
					' ',
					FANCYSTATWIDTH - strlen($stat_title . $stat_string),
				) .
				$stat_string
		: $stat_string;
}

/**
 * Zaregistrovať inštrukciu pre štatistiky.
 *
 * @param string $op Inštrukcia
 *
 * @return void
 */
function register_instruction(string $op): void {
	global $GINFO;

	if (array_key_exists($op, $GINFO['opstat'])) {
		// Inštrukcia je už definovaná
		$GINFO['opstat'][$op]++;
	} else {
		// Pridať inštrukciu do zoznamu
		$GINFO['opstat'][$op] = 1;
	}
}

/**
 * Zaregistrovať náveštie a validovať skoky na toto náveštie.
 *
 * @param string $label Náveštie
 *
 * @return void
 */
function register_label(string $label): void {
	global $GINFO;

	// Náveštie je už definované
	if (array_key_exists($label, $GINFO['labels']['def'])) {
		return;
	}

	// Pridať náveštie do zoznamu
	array_push($GINFO['labels']['def'], $label);

	// Validovať skoky na toto náveštie
	$fwjump_count = array_count_values($GINFO['labels']['ndef'])[$label] ?? 0;
	$GINFO['jumps']['fw'] += $fwjump_count;
	$GINFO['labels']['ndef'] = array_filter(
		$GINFO['labels']['ndef'],
		function ($val) use ($label) {
			return $val !== $label;
		},
	);
}

/**
 * Zaregistrovať skok na náveštie
 *
 * @param string $label Náveštie
 *
 * @return void
 */
function register_jump(string $label): void {
	global $GINFO;

	// Náveštie je v zozname => skok dozadu
	if (array_search($label, $GINFO['labels']['def']) !== false) {
		$GINFO['jumps']['bw']++;
		return;
	}

	// Náveštie nie je v zozname => skok dopredu alebo chybný skok
	array_push($GINFO['labels']['ndef'], $label);
}

/**
 * Vyhodenie chyby a ukončenie programu.
 *
 * @param string $ecode Typ chyby
 * @param int|null $ln Číslo riadku chyby
 * @param string $msg Správa
 *
 * @return void
 */
function throw_err(string $ecode, ?int $ln, string $msg): void {
	global $GINFO;

	$color = $GINFO['fancy'];
	$err_string = '';

	$ERR = $color ? "\033[31;49;1mERR!\033[0m" : 'ERR!';
	$CODE = $color ? "\033[35;49mcode\033[0m" : 'code';
	$err_string .= "$ERR $CODE $ecode\n";
	$LINE = $color ? "\033[35;49mline\033[0m" : 'line';
	$err_string .= $ln ? "$ERR $LINE $ln\n" : '';
	$err_string .= "$ERR $msg";

	error_log($err_string);
	exit(RETCODE[$ecode]);
}
