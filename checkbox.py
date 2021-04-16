#!/usr/bin/env python

import argparse
import tkinter as tk

from pathlib import Path
from functools import partial


def parse_flags():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-x", type=int, required=True,
        help="x position for the window"
    )
    parser.add_argument(
        "-y", type=int, required=True,
        help="y position for the window"
    )
    return parser.parse_args()


def print_value(var):
    check_file = Path("/tmp/casper_checkbox_value")
    with open(str(check_file), "w") as fout:
        fout.write(str(bool(var.get())))


def main(x, y):
    window = tk.Tk()
    window.title("Casper checkbox")
    window.geometry(f"300x5+{x}+{y + 10}")
    var = tk.IntVar()
    c1 = tk.Checkbutton(
        window,
        text="Keep window open when it looses focus",
        variable=var,
        onvalue=1,
        offvalue=0,
        command=partial(print_value, var),
    )
    c1.pack()
    window.mainloop()


if __name__ == "__main__":
    main(**vars(parse_flags()))
