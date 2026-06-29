#!/usr/bin/env bash

TEXT="$(cat $HOME/Work/dzencode.ua/test-task-v2/task.txt)"

for i in {0001..0050}; do
  curl -L -o ./images/$i.png "https://picsum.photos/800/600"
done

for i in {0051..0100}; do
  curl -L -o ./images/$i.png "https://picsum.photos/200/100"
done
