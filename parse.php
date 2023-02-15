<?php

/**
 * IPP projekt 2023, časť 1
 *
 * Lexikálny a syntaktický analyzátor, a prevodník
 * zdrojového kódu v IPPcode23 do XML reprezentácie.
 * @author Onegen Something <xonege99@vutbr.cz>
 */

ini_set('display_errors', 'stderr');

include 'lib_parse/ippc_scanner.php';

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

/** @var \ArrayObject VALID_OPTS Zoznam rozpoznávaných parametrov */
define('VALID_OPTS', [
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
	if (!in_array($opt, array_keys(VALID_OPTS))) {
		continue;
	}

	if (VALID_OPTS[$opt] == 'req' && !$val) {
		// Parameter s povinnou hodnotou bez hodnoty
		throw_err('EPARAM', null, "Missing value for option --$opt");
	} elseif (VALID_OPTS[$opt] == 'no' && $val) {
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
$XML = ippcXML_new_root();

/* Spracovanie vstupu */
for ($lineno = 0; ($line = fgets(STDIN)); $lineno++) {
	$GINFO['lines'] = $lineno + 1;
	ippc_parse_line($line);
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

	$stat_string = ippcstat_collect();
	fwrite($stat_file, $stat_string);
	fclose($stat_file);
}

/* Výpis XML reprezentácie kódu */
echo ippcXML_asXML(true);
exit(RETCODE['OK']);

/* Pomocné funkcie */

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
