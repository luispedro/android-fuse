# Android-fuse

Mounts an android device using FUSE.

Requires [fusepy](https://github.com/terencehonles/fusepy) and that `adb` be
present in the PATH.

This works by calling `adb shell ls` and `adb pull` to get information/data.

Usage:

    python android-fuse.py <mount-point>

THIS IS ALPHA SOFTWARE AND MAY DO BAD THINGS TO YOUR PHONE, INCLUDING
DESTROYING DATA!

A file called `tmpfile.tmp` will appear in the working directory (and will be
removed later unless there is a crash). Do not remove it or mess with it while
the program is running.

# What works & what does not

- You list directories and 'cd' into them
- You can read files from the phone, including symlinks
- `du -sh somefile.txt` will work as expected
- You can delete files from the phone
- Creating files and directories is not implemented
- Files with spaces do not work


Licence: MIT
Author: [Luis Pedro Coelho](http://luispedro.org) [luis@luispedro.org](mailto:luis@luispedro.org)

