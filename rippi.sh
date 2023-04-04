#!/bin/zsh
#
## @file ippi.sh
## @brief Spúšťač parsera aj interpréta IPPcode23
## @author Onegen Something <xonege99@vutbr.cz>
## @note Toto je iba riced-up skriptík pre seba, nie súčasť riešenia.
##
## @requires bat (https://github.com/sharkdp/bat)
## @requires Nerd Fonts (https://www.nerdfonts.com)
##

cleanup() {
	if [ -f "$temp_xml" ]; then
		rm "$temp_xml"
	fi
	if [ -f "$input" ]; then
		rm "$input"
	fi
}

input=""
quiet_flag=0
iopt=""
iin=""

while getopts "heqd" opt; do
	case $opt in
	h)
		echo "\033[35;1m﬙ RunIPPIntrpr \033[37m(by Onegen)\033[0m"
		echo "    \033[30mRiced-up spúštač IPPcode23 zdrojáka použitím \033[34m parse.php \033[30m \033[36m interpret.py\033[30m.\033[0m"
		echo "      \033[37m./ippi.sh [OPTIONS] zdroják <vstup\033[0m"
		echo ""
		echo "    \033[32m-h\033[0m     \033[30mZobrazí túto nápovedu a ukončí skript\033[0m"
		echo "    \033[32m-e\033[0m     \033[30mPrádzny vstup (inak bude očakávaní vstup na stdin)\033[0m"
		echo "    \033[32m-q\033[0m     \033[30mNevypisovať medzikód a XML\033[0m"
		echo "    \033[32m-d\033[0m     \033[30mRozšírený výstup interpréta\033[0m"
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
	\?)
		echo "  \033[31;1mwtf getopt \033[37m-$OPTARG\033[0m"
		exit 1
		;;
	esac
done
shift $((OPTIND - 1))
if [ $# -eq 0 ]; then
	echo "  \033[31;1mgde sauce?\033[0m"
	exit 1
else
	zdrojak="$1"
fi
if [ ! -f "$zdrojak" ]; then
	echo "  \033[31;1mgde sauce?\033[0m"
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

# ==== PARSER ====

echo "\033[37;1mSpúštam \033[34m parse.php\033[37m...\033[0m"
temp_xml=$(mktemp)
php81 parse.php <"$zdrojak" >"$temp_xml"
parse_status=$?
if [ $parse_status -eq 0 ]; then
	if [ $quiet_flag -eq 0 ]; then
		bat -Pf -r :20 --theme TwoDark --language xml "$temp_xml"
	fi
	echo "  \033[31;1m  \033[32m$parse_status\033[0m"
else
	cleanup
	echo ""
	echo "  \033[37;1mﮊ  \033[31m$parse_status\033[0m"
	exit $parse_status
fi

# ==== INTERPRET ====

echo ""
echo "\033[37;1mSpúštam \033[36m interpret.py\033[37m...\033[0m"
python interpret.py $iopt --source="$temp_xml" --input="$iin"
interpret_status=$?

# ==== CLEANUP ====

cleanup
if [ $interpret_status -eq 0 ]; then
	echo ""
	echo "  \033[31;1m  \033[32m$interpret_status\033[0m"
else
	echo ""
	echo "  \033[37;1mﮊ  \033[31m$interpret_status\033[0m"
fi
exit $interpret_status
