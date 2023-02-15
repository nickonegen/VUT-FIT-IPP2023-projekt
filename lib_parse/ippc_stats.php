<?php

/**
 * Pomocná knižnica pre získavanie štatistík
 * (rozšírenie STATP)
 * @author Onegen Something <xonege99@vutbr.cz>
 */

/** @var int FANCY_STAT_WIDTH Šírka textového "fancy" výstupu štatistík */
define('FANCY_STAT_WIDTH', 70);

/**
 * Vypísať reťazec zo štatistík
 *
 * @return string Štatistiky
 */
function ippcstat_collect(): string {
	global $GINFO;
	$fancy = $GINFO['fancy'];
	$stat_string = '';

	// Výpis štatistík
	$total = count($GINFO['statord']);
	$i = 0;
	foreach ($GINFO['statord'] as [$opt, $val]) {
		$stat_string .= ippcstat_obtain($opt, $val);
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

	return $stat_string;
}

/**
 * Získanie jednej štatistiky.
 *
 * @param string $stat_name Názov štatistiky (parameter)
 * @param string|null $stat_optval Hodnota parametra (pre --print)
 *
 * @return string Riadok štatistiky
 */
function ippcstat_obtain(string $stat_name, ?string $opt_val): string {
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
			$stat_string .= $opt_val;
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
					FANCY_STAT_WIDTH - strlen($stat_title . $stat_string),
				) .
				$stat_string
		: $stat_string;
}

/**
 * Zaregistrovať inštrukciu pre štatistiky.
 *
 * @param string $instr Inštrukcia
 *
 * @return void
 */
function ippcstat_reg_instruction(string $instr): void {
	global $GINFO;

	if (array_key_exists($instr, $GINFO['opstat'])) {
		// Inštrukcia je už definovaná
		$GINFO['opstat'][$instr]++;
	} else {
		// Pridať inštrukciu do zoznamu
		$GINFO['opstat'][$instr] = 1;
	}
}

/**
 * Zaregistrovať náveštie a validovať skoky na toto náveštie.
 *
 * @param string $label Náveštie
 *
 * @return void
 */
function ippcstat_reg_label(string $label): void {
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
function ippcstat_reg_jump(string $label): void {
	global $GINFO;

	// Náveštie je v zozname => skok dozadu
	if (array_search($label, $GINFO['labels']['def']) !== false) {
		$GINFO['jumps']['bw']++;
		return;
	}

	// Náveštie nie je v zozname => skok dopredu alebo chybný skok
	array_push($GINFO['labels']['ndef'], $label);
}
