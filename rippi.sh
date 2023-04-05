#!/bin/sh
#
## @file rippi.sh
## @brief Spúšťač parsera aj interpréta IPPcode23
## @author Onegen Something <xonege99@vutbr.cz>
## @requires bat (https://github.com/sharkdp/bat)
## @requires Nerd Fonts (https://www.nerdfonts.com)
## @note Toto je iba skriptík pre seba, nie súčasť riešenia.
##

export POSIXLY_CORRECT=no LANG=sk_SK.UTF-8
cleanup() { [ -f "$temp_xml" ] && rm "$temp_xml"; [ -f "$input" ] && rm "$input"; }
do_parse=1 do_interpret=1 quiet_flag=0 plain_flag=0 help_flag=0 statp_flag=0 stati_flag=0 idbg_flag=0 pleg_flag=0
input="" popt="" iopt="" iin="" batopt="-Pf --theme TwoDark"
OPTIONS="heXNqpsdS" LONGOPTIONS="help,no-input,no-parse,no-run,quiet,statp,stati,iDEBUG,pLEGACY,pHELP,iHELP"
PARSED=$(getopt --options=$OPTIONS --longoptions=$LONGOPTIONS --name "$0" -- "$@")
eval set -- "$PARSED"
while true; do
	case $1 in
	-h | --help)
		echo -e "\033[35;1mﳨ RicerunIPPIntrpr ﬙ \033[37m(by Onegen)\033[0m"
		echo -e "    \033[37mRiced-up spúštač IPPcode23 zdrojáka použitím \033[34m parse.php \033[37m \033[36m interpret.py\033[90m.\033[0m"
		echo -e "      \033[37;1m./rippi.sh [OPTIONS] zdroják <vstup\033[0m\n"
		echo -e "    \033[32m-h\033[0m,\033[32m--help\033[0m       \033[37mzobrazí túto nápovedu a ukončí skript\033[0m"
		echo -e "    \033[32m-e\033[0m,\033[32m--no-input\033[0m   \033[37mprázdny vstup (neočakávať/ignorovať stdin)\033[0m"
		echo -e "    \033[32m-X\033[0m,\033[32m--no-parse\033[0m   \033[37mzdroják je XML, preskočiť parser\033[0m"
		echo -e "    \033[32m-N\033[0m,\033[32m--no-run\033[0m     \033[37mpreskočiť interprét, spustiť iba parser\033[0m"
		echo -e "    \033[32m-q\033[0m,\033[32m--quiet\033[0m      \033[37mtichší výstup, nevypisovať medzikód a XML\033[0m"
		echo -e "    \033[32m-p\033[0m              \033[37mnepoužívať --fancier opt\033[0m\n"
		echo -e "    \033[32m-s\033[0m,\033[32m--statp\033[0m      \033[37mvypísať štatistiky parsera do 'statp.txt'\033[0m"
		echo -e "    \033[32m-S\033[0m,\033[32m--stati\033[0m      \033[37mvypísať štatistiky interpréta do 'stati.txt'\033[0m"
		echo -e "    \033[32m-d\033[0m,\033[32m--iDEBUG\033[0m     \033[37mrozšírený výstup interpréta pre ladenie\033[0m"
		echo -e "    \033[32m--pLEGACY\033[0m       \033[37mnastaviť parser na legacy mód (bez STACK/FLOAT)\033[0m";
		echo -e "    \033[32m--pHELP\033[0m         \033[37mzobraziť nápovedu parsera\033[0m";
		echo -e "    \033[32m--iHELP\033[0m         \033[37mzobraziť nápovedu interpréta\033[0m"; exit 0;;
	-e | --no-input) iin="/dev/null"; shift;;
	-X | --no-parse) do_parse=0; shift;;
	-N | --no-run) do_interpret=0; shift;;
	-q | --quiet) quiet_flag=1; shift;;
	-p) plain_flag=1; shift;;
	-s | --statp) statp_flag=1; shift;;
	-S | --stati) stati_flag=1; shift;;
	-d | --iDEBUG) idbg_flag=1; shift;;
	--pLEGACY) pleg_flag=1; shift;;
	--pHELP) help_flag=1; shift;;
	--iHELP) help_flag=2; shift;;
	--) shift; break;;
	*) echo -e "  \033[31;1mwtf getopt \033[37m-$OPTARG\033[0m"; exit 1;;
	esac
done
shift $((OPTIND - 1))
[ $help_flag -eq 1 ] && { php parse.php --help; exit 0; }
[ $help_flag -eq 2 ] && { python3.10 interpret.py --help; exit 0; }
[ $# -eq 0 ] && { echo -e "  \033[31;1mgde sauce?\033[0m"; exit 1; } || zdrojak="$1"
[ ! -f "$zdrojak" ] && { echo -e "  \033[31;1mgde sauce?\033[0m"; exit 1; }
[ $do_parse -eq 0 ] && [ $do_interpret -eq 0 ] && { echo -e "  \033[31;1m-X -I? run it yourself if you think ur so smart\033[0m"; exit 1; }
[ -z "$iin" ] && { input=$(mktemp); cat >"$input"; iin="$input"; }
[ $statp_flag -eq 1 ] && popt="${popt} --stats=statp.txt --eol --loc --comments --labels --jumps --fwjumps --backjumps --badjumps --frequent --eol"
[ $stati_flag -eq 1 ] && iopt="${iopt} --stats=stati.txt --eol --insts --hot --vars --frequent --eol"
[ $idbg_flag -eq 1 ] && iopt="${iopt} -d"
[ $pleg_flag -eq 1 ] && popt="${popt} --legacy"
[ $quiet_flag -eq 0 ] && bat $batopt -r :15  "$zdrojak"
[ $do_interpret -eq 1 ] && batopt="${batopt} -r :20"
echo -e "\033[35;1mﳨ RicerunIPPIntrpr \033[37;3mv0.4.20\033[0m"
echo -e "\033[37m---------------------------\033[0m"
[ $do_parse -eq 1 ] && {
	temp_xml=$(mktemp)
	[ $plain_flag -eq 0 ] && popt="${popt} --fancier"
	echo -e "\033[37;1mSpúštam \033[34m parse.php\033[37m...\033[0m"
	php81 parse.php $popt <"$zdrojak" >"$temp_xml"
	parse_status=$?
	if [ $parse_status -eq 0 ]; then
		[ $quiet_flag -eq 0 ] && bat $batopt --language xml "$temp_xml"
		[ $do_interpret -eq 0 ] && echo ""
		echo -e "  \033[31;1m  \033[32m$parse_status\033[0m"
	else
		cleanup; echo ""; echo -e "  \033[37;1mﮊ  \033[31m$parse_status\033[0m"; exit $parse_status
	fi
} || { temp_xml=$(mktemp); cat "$zdrojak" >"$temp_xml"; }
[ $do_interpret -eq 1 ] && {
	[ $do_parse -eq 1 ] && echo ""
	[ $plain_flag -eq 0 ] && iopt="${iopt} --fancier"
	echo -e "\033[37;1mSpúštam \033[36m interpret.py\033[37m...\033[0m"
	python interpret.py $iopt --source="$temp_xml" --input="$iin"
	interpret_status=$?
	[ $interpret_status -eq 0 ] && echo -e "\n  \033[31;1m  \033[32m$interpret_status\033[0m" || echo -e "\n  \033[37;1mﮊ  \033[31m$interpret_status\033[0m"
	cleanup
	exit "$interpret_status"
} || { cleanup; exit "$parse_status"; }
