#!/bin/sh
#
## @file ippi.sh
## @brief Spúšťač parsera aj interpréta IPPcode23
## @author Onegen Something <xonege99@vutbr.cz>
## @note Toto je iba riced-up skriptík pre seba, nie súčasť riešenia.
## @requires bat (https://github.com/sharkdp/bat)
## @requires Nerd Fonts (https://www.nerdfonts.com)
##

export POSIXLY_CORRECT=no
export LANG=sk_SK.UTF-8

cleanup() {
	if [ -f "$temp_xml" ]; then
		rm "$temp_xml"
	fi
	if [ -f "$input" ]; then
		rm "$input"
	fi
}

input=""
do_parse=1
do_interpret=1
quiet_flag=0
iopt=""
iin=""

while getopts "heqdXI" opt; do
	case $opt in
	h)
		echo -e "\033[35;1mﳨ RicerunIPPIntrpr ﬙ \033[37m(by Onegen)\033[0m"
		echo -e "    \033[37mRiced-up spúštač IPPcode23 zdrojáka použitím \033[34m parse.php \033[90m \033[36m interpret.py\033[90m.\033[0m"
		echo -e "      \033[37;1m./rippi.sh [OPTIONS] zdroják <vstup\033[0m"
		echo ""
		echo -e "    \033[32m-h\033[0m     \033[37mHelp: zobrazí túto nápovedu a ukončí skript\033[0m"
		echo -e "    \033[32m-X\033[0m     \033[37mXml input: preskočiť parser\033[0m"
		echo -e "    \033[32m-N\033[0m     \033[37mNo run: preskočiť interprét\033[0m"
		echo -e "    \033[32m-e\033[0m     \033[37mEmpty: prádzny vstup (neočakávať vstup na stdin)\033[0m"
		echo -e "    \033[32m-q\033[0m     \033[37mQuiet: nevypisovať medzikód a XML\033[0m"
		echo -e "    \033[32m-d\033[0m     \033[37mDebug: rozšírený výstup interpréta\033[0m"
		exit 0
		;;
	e)
		iin="/dev/null"
		;;
	q)
		quiet_flag=1
		;;
	d)
		iopt="-d"
		;;
	X)
		do_parse=0
		;;
	I)
		do_interpret=0
		;;
	\?)
		echo -e "  \033[31;1mwtf getopt \033[37m-$OPTARG\033[0m"
		exit 1
		;;
	esac
done
shift $((OPTIND - 1))
if [ $# -eq 0 ]; then
	echo -e "  \033[31;1mgde sauce?\033[0m"
	exit 1
else
	zdrojak="$1"
fi
if [ ! -f "$zdrojak" ]; then
	echo -e "  \033[31;1mgde sauce?\033[0m"
	exit 1
fi
if [ $do_parse -eq 0 ] && [ $do_interpret -eq 0 ]; then
	echo -e "  \033[31;1m-X -I? run it yourself if you think ur so smart\033[0m"
	exit 1
fi
if [ -z "$iin" ]; then
	input=$(mktemp)
	cat >"$input"
	iin="$input"
fi
if [ $quiet_flag -eq 0 ]; then
	bat -Pf -r :15 --theme TwoDark "$zdrojak"
fi
echo -e "\033[35;1mﳨ RicerunIPPIntrpr \033[37;3mv0.4.20\033[0m"
echo -e "\033[37m---------------------------\033[0m"

# ==== PARSER ====

if [ $do_parse -eq 1 ]; then
	echo -e "\033[37;1mSpúštam \033[34m parse.php\033[37m...\033[0m"
	temp_xml=$(mktemp)
	php81 parse.php <"$zdrojak" >"$temp_xml"
	parse_status=$?
	if [ $parse_status -eq 0 ]; then
		if [ $quiet_flag -eq 0 ]; then
			bat -Pf -r :20 --theme TwoDark --language xml "$temp_xml"
		fi
		if [ $do_interpret -eq 0 ]; then
			echo ""
		fi
		echo -e "  \033[31;1m  \033[32m$parse_status\033[0m"
	else
		cleanup
		echo ""
		echo -e "  \033[37;1mﮊ  \033[31m$parse_status\033[0m"
		exit $parse_status
	fi
else
	temp_xml=$(mktemp)
	cat "$zdrojak" >"$temp_xml"
fi

# ==== INTERPRET ====

if [ $do_interpret -eq 1 ]; then
	if [ $do_parse -eq 1 ]; then
		echo ""
	fi
	echo -e "\033[37;1mSpúštam \033[36m interpret.py\033[37m...\033[0m"
	python interpret.py $iopt --source="$temp_xml" --input="$iin"
	interpret_status=$?
	if [ $interpret_status -eq 0 ]; then
		echo ""
		echo -e "  \033[31;1m  \033[32m$interpret_status\033[0m"
	else
		echo ""
		echo -e "  \033[37;1mﮊ  \033[31m$interpret_status\033[0m"
	fi
	cleanup
	exit $interpret_status
else
	cleanup
	exit $parse_status
fi
