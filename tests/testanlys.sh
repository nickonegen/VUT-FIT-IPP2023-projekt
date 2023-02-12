#!/bin/bash

failed_tests=()
successful_tests=0
failed_count=0

tests=$(find ./tests/parser -type f -name "*.src")

for test in $tests
do
  path=${test%.src}

  php81 parse.php < "$test" > /dev/null 2>&1
  RETURN_CODE=$?

  if [ "$RETURN_CODE" -ne "$(cat "$path.rc")" ]; then
    echo -e "$path : FAIL"
    failed_tests+=("$path")
    ((failed_count++))
  else
    echo -e "$path : OK"
    ((successful_tests++))
  fi
done

echo ""
echo "=============================="
echo ""
echo "Total tests: $(($successful_tests + $failed_count))"
echo "Successful tests: $successful_tests"
echo "Failed tests: $failed_count"

if [ $failed_count -gt 0 ]; then
  echo "Failed tests:"
  for test in "${failed_tests[@]}"
  do
    echo "  $test"
  done
fi

if [ $failed_count -gt 0 ]; then
  exit 1
fi
