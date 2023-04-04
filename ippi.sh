#!/bin/zsh
#
## @file ippi.sh
## @brief Spúšťač parsera aj interpréta IPPcode23
## @author Onegen Something <xonege99@vutbr.cz>
## @note Toto je skriptík iba pre seba, nie súčasť riešenia
##
## @requires bat (https://github.com/sharkdp/bat)
## @requires Nerd Fonts (https://www.nerdfonts.com)
##

if [ "$#" -lt 1 ]; then
	echo "  \033[31;1mgde sauce?\033[0m"
	exit 1
fi

zdrojak="$1"
bat -Pf --theme TwoDark "$zdrojak"

# ==== PARSER ====

echo ""
echo "\033[37;1mSpúštam \033[34m parse.php\033[37m...\033[0m"

temp_xml=$(mktemp)

php81 parse.php <"$zdrojak" >"$temp_xml"
parse_status=$?

if [ $parse_status -eq 0 ]; then
	bat -Pf --theme TwoDark --language xml "$temp_xml"
else
	rm "$temp_xml"
	exit $parse_status
fi

# ==== INTERPRET ====

echo ""
echo "\033[37;1mSpúštam \033[36m interpret.py\033[37m...\033[0m"
python interpret.py -d --source="$temp_xml"
interpret_status=$?

# ==== CLEANUP ====

rm "$temp_xml"

if [ $interpret_status -eq 0 ]; then
	echo ""
	echo "  \033[31;1m  \033[32m$interpret_status\033[0m"
else
	echo ""
	echo "  \033[37;1mﮊ  \033[31m$interpret_status\033[0m"
fi

exit $interpret_status
