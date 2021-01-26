# casper-container
A drop-down, generic container for i3wm

## Installation
* Clone the repo
* Install python packages (`[sudo] pip install -r requirements.txt`)
* Install the container (`make install`, will default to `$HOME/.config`)
* [Optionally] Launch with `$HOME/.config/casper/launch.sh`
* Register a shortcut for i3 (i.e.: `bindsym Control+Q exec --no-startup-id $HOME/.config/casper/launch.sh`)
* Ready to go!

## Configuration
By default, the container is hidden when it looses focus. To customize it go see `./default.config`

## Why
Because I've used Xfce4-terminal's drop-down option for a long time, and I
wanted to have several terminals side-by-side

## Caveats
By now, only xfce4-terminal's are allowed to be in the container. This may
change in the future if more applications are desired. To so, those must accept
a `--title` option (to be swallowed by the i3-layout), or a we must come up
with a new way to re-structure windows inside containers (class, instance...).

## Contributing
Any PR/bug report is welcome, just be as explicit as possible with your
request!
