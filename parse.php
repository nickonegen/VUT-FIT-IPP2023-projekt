<?php

/**
 * IPP projekt, časť 1
 * 
 * Lexikálny a syntaktický analyzátor IPPcode23 na XML
 * @author Onegen Something <xonege99@vutbr.cz>
 * 
 * @param bool $help Vlajka '-help' na zobrazenie nápovedy
 */

/** @var \ArrayObject RETURNCODE Návratový kód */
define('RETURNCODE', array(
	'OK'			=> 0,
	'EPARAM'	=> 10,
	'ENOENT'	=> 11,
	'EWRITE'	=> 12,
	'ENOHEAD'	=> 21,
	'EOPCODE'	=> 22,
	'EANLYS'	=> 23,
	'EINT'		=> 99
));

exit(RETURNCODE['OK']);