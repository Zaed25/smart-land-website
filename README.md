# Smart Land website

Static Arabic (RTL) website for Smart Land, a tech company founded in 2011.
Homework for BMM601 (Multimedia), SVU, F25.

Live site: https://zaed25.github.io/smart-land-website/

## Structure

- `index.html`, `about.html`, `services.html`, `projects.html`, `contact.html`: the pages
- `css/style.css`: all styles (RTL layout, responsive breakpoints at 980, 820 and 600 px)
- `js/main.js`: mobile menu, scroll animations, counters, project filter and details window, video window, form checks
- `assets/img`: images in AVIF and WEBP at three widths each
- `assets/video`: three MP4 videos with WebVTT captions and posters
- `assets/logo`: the logo in SVG
- `tools/process_images.sh`: crop, colour correction and conversion of the images
- `tools/make_videos.py`: video montage (clips, title cards, voice-over, music, captions)

Images and video clips were generated with Google Flow, then edited with the scripts in `tools/`.

## Author

Mohammed Zaid Al-Nahhas (mhd_zaid_211096), SVU ITE, F25, C5.
