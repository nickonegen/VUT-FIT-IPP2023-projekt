<?php

/**
 * Pomocná knižnica pre tvorbu XML reprezentácie IPPcode23
 * @author Onegen Something <xonege99@vutbr.cz>
 */

/**
 * Vytvoriť základ XML reprezentácie IPPcode23
 *
 * @return SimpleXMLElement
 */
function ippcXML_new_root(): SimpleXMLElement {
	return new SimpleXMLElement(
		'<?xml version="1.0" encoding="UTF-8"?><program language="IPPcode23"></program>',
	);
}

/**
 * Vytvoriť XML reťazec z XML reprezentácie IPPcode23
 *
 * @param ?bool $format Formátovať XML reťazec?
 *
 * @return string XML reťazec
 */
function ippcXML_asXML(bool $format = false): string {
	global $XML;

	if (!$format) {
		return $XML->asXML();
	}

	// @see https://stackoverflow.com/a/16282331
	$dom = new DOMDocument('1.0');
	$dom->preserveWhiteSpace = false;
	$dom->formatOutput = true;
	$dom->loadXML($XML->asXML());
	return $dom->saveXML();
}

/**
 * Pridať novú inštrukciu do XML reprezentácie IPPcode23
 *
 * @param string $name Názov inštrukcie
 *
 * @return SimpleXMLElement
 */
function ippcXML_add_instruction(string $name): SimpleXMLElement {
	global $GINFO;
	global $XML;

	$instruction = $XML->addChild('instruction');
	$instruction->addAttribute('order', $GINFO['i_lines']);
	$instruction->addAttribute('opcode', $name);
	return $instruction;
}

/**
 * Pridať prádzny argument do XML reprezentácie IPPcode23
 *
 * @param SimpleXMLElement $instruction XML element inštrukcie
 * @param int $order Poradie argumentu
 *
 * @return SimpleXMLElement
 */
function ippcXML_add_arg(SimpleXMLElement $instruction, int $order) {
	return $instruction->addChild('arg' . $order);
}

/**
 * Nastaviť XML element argumentu na premennú s danou hodnotou
 *
 * @param SimpleXMLElement $arg_xml XML element argumentu
 * @param string $value Hodnota premennej
 *
 * @return SimpleXMLElement
 */
function ippcXML_make_variable(SimpleXMLElement $arg_xml, string $value) {
	$arg_xml->addAttribute('type', 'var');
	$arg_xml[0] = $value;
	return $arg_xml;
}

/**
 * Nastaviť XML element argumentu na konštantnú hodnotu
 *
 * @param SimpleXMLElement $arg_xml XML element argumentu
 * @param string $type Typ konštanty
 * @param string $value Hodnota konštanty
 *
 * @return SimpleXMLElement
 */
function ippcXML_make_constant(
	SimpleXMLElement $arg_xml,
	string $type,
	string $value,
) {
	$arg_xml->addAttribute('type', strtolower($type));
	$arg_xml[0] = $value;
	return $arg_xml;
}

/**
 * Nastaviť XML element argumentu na náveštie
 *
 * @param SimpleXMLElement $arg_xml XML element argumentu
 * @param string $name Názov náveštia
 *
 * @return SimpleXMLElement
 */
function ippcXML_make_label(SimpleXMLElement $arg_xml, string $name) {
	$arg_xml->addAttribute('type', 'label');
	$arg_xml[0] = $name;
	return $arg_xml;
}

/**
 * Nastaviť XML element argumentu na typ
 *
 * @param SimpleXMLElement $arg_xml XML element argumentu
 * @param string $type Typ
 *
 * @return SimpleXMLElement
 */
function ippcXML_make_type(SimpleXMLElement $arg_xml, string $type) {
	$arg_xml->addAttribute('type', 'type');
	$arg_xml[0] = $type;
	return $arg_xml;
}
