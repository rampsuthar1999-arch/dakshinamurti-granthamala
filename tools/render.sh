#!/bin/bash
# render pages $1..$2 as grayscale webp
for ((p=$1; p<=$2; p++)); do
  pdftoppm -r 110 -gray -png -f $p -l $p /mnt/user-data/uploads/82_Pancadashi.pdf /home/claude/work/img/t$p
  f=$(ls /home/claude/work/img/t$p-*.png)
  python3 -c "
from PIL import Image; import sys
im=Image.open(sys.argv[1]); im.save(sys.argv[2],'WEBP',quality=40,method=4)" "$f" /home/claude/work/img/$p.webp
  rm "$f"
done
