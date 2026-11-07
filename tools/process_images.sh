#!/bin/bash
# Image pipeline for the Smart Land site.
#   source (jpg from Google Flow, or a frame taken from a Flow video)
#   -> crop to the layout ratio -> colour/contrast correction -> sharpen
#   -> resize to 3 widths -> AVIF + WEBP (no JPG/PNG is published)
# usage: SRC=../../source_media ./process_images.sh
set -euo pipefail
cd "$(dirname "$0")"
SRC=${SRC:-../../source_media}
OUT=../assets/img
TMP=$(mktemp -d)
mkdir -p "$OUT"

# name | source | frame second (videos only, - for images) | ratio | widths
LIST="
hero        | img_hero_b.jpg       | - | 16:9 | 640 1024 1376
about       | img_hero_a.jpg       | - | 16:9 | 640 1024 1376
team        | img_team_a.jpg       | - | 16:9 | 640 1024 1376
team2       | img_team_b.jpg       | - | 4:3  | 480 800 1024
success     | img_success.jpg      | - | 16:9 | 640 1024 1376
contact     | img_building.jpg     | - | 16:9 | 640 1024 1376
welcome     | img_welcome.jpg      | - | 4:3  | 480 800 1024
smartsignal | v2_c1_signing.mp4    | 4.5 | 4:3 | 480 800 960
mykey       | v3_c1_mykey.mp4      | 1.5 | 4:3 | 480 800 960
sada        | v3_c2_sada.mp4       | 3.6 | 4:3 | 480 800 960
ai          | v1_c3_ai.mp4         | 7.5 | 4:3 | 480 800 960
mission     | v1_c5_handshake.mp4  | 6.0 | 4:3 | 480 800 960
wave        | v2_c2_phone.mp4      | 7.2 | 4:3 | 480 800 960
"

echo "$LIST" | while IFS='|' read -r name src sec ratio widths; do
  name=$(echo $name); src=$(echo $src); sec=$(echo $sec); ratio=$(echo $ratio)
  [ -z "$name" ] && continue
  in="$TMP/$name.png"
  if [ "$sec" = "-" ]; then
    magick "$SRC/$src" "$in"
  else
    ffmpeg -v error -y -ss "$sec" -i "$SRC/$src" -frames:v 1 "$in"       # still frame from the video
  fi
  # crop to the ratio from the centre, then colour correction and sharpening
  magick "$in" -gravity center -crop "$ratio" +repage \
         -modulate 100,108,100 -brightness-contrast 2x6 \
         -unsharp 0x0.8+0.6+0.02 -strip "$TMP/${name}_fixed.png"
  for w in $widths; do
    magick "$TMP/${name}_fixed.png" -resize "${w}x>" "$TMP/${name}-$w.png"
    cwebp -quiet -q 78 -m 6 "$TMP/${name}-$w.png" -o "$OUT/${name}-$w.webp"
    avifenc -q 55 -s 6 "$TMP/${name}-$w.png" "$OUT/${name}-$w.avif" >/dev/null
  done
  echo "$name: $(ls "$OUT"/${name}-* | wc -l | tr -d ' ') files"
done
rm -rf "$TMP"
du -ch "$OUT"/* | tail -1
