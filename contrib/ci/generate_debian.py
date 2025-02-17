#!/usr/bin/python3
#
# Copyright (C) 2017 Dell, Inc.
#
# SPDX-License-Identifier: LGPL-2.1+
#
import os
import sys
from fwupd_setup_helpers import get_build_dependencies


def parse_control_dependencies(requested_type):
    TARGET = os.getenv("OS")
    QUBES = os.getenv("QUBES")

    if TARGET == "":
        print("Missing OS environment variable")
        sys.exit(1)
    OS = TARGET
    SUBOS = ""
    if TARGET:
        split = TARGET.split("-")
        if len(split) >= 2:
            OS = split[0]
            SUBOS = split[1]
    else:
        import lsb_release

        OS = lsb_release.get_distro_information()["ID"].lower()
        import platform

        SUBOS = platform.machine()

    return get_build_dependencies(OS, SUBOS), QUBES


def update_debian_control(target):
    control_in = os.path.join(target, "control.in")
    control_out = os.path.join(target, "control")

    if not os.path.exists(control_in):
        print("Missing file %s" % control_in)
        sys.exit(1)

    with open(control_in, "r") as rfd:
        lines = rfd.readlines()

    deps, QUBES = parse_control_dependencies("build")
    deps.sort()

    if QUBES:
        lines += "\n"
        control_qubes_in = os.path.join(target, "control.qubes.in")
        with open(control_qubes_in, "r") as rfd:
            lines += rfd.readlines()

    with open(control_out, "w") as wfd:
        for line in lines:
            if line.startswith("Build-Depends: %%%DYNAMIC%%%"):
                wfd.write("Build-Depends:\n")
                for i in range(0, len(deps)):
                    wfd.write("\t%s,\n" % deps[i])
            elif "fwupd-qubes-vm-whonix" in line and not QUBES:
                break
            else:
                wfd.write(line)


def update_debian_copyright(directory):
    copyright_in = os.path.join(directory, "copyright.in")
    copyright_out = os.path.join(directory, "copyright")

    if not os.path.exists(copyright_in):
        print("Missing file %s" % copyright_in)
        sys.exit(1)

    # Assume all files are remaining LGPL-2.1+
    copyrights = []
    for root, dirs, files in os.walk("."):
        for file in files:
            target = os.path.join(root, file)
            # skip translations and license file
            if target.startswith("./po/") or file == "COPYING":
                continue
            try:
                with open(target, "r") as rfd:
                    # read about the first few lines of the file only
                    lines = rfd.readlines(220)
            except UnicodeDecodeError:
                continue
            except FileNotFoundError:
                continue
            for line in lines:
                if "Copyright (C) " in line:
                    parts = line.split("Copyright (C)")[
                        1
                    ].strip()  # split out the copyright header
                    partition = parts.partition(" ")[2]  # remove the year string
                    copyrights += ["%s" % partition]
    copyrights = "\n\t   ".join(sorted(set(copyrights)))
    with open(copyright_in, "r") as rfd:
        lines = rfd.readlines()

    with open(copyright_out, "w") as wfd:
        for line in lines:
            if line.startswith("%%%DYNAMIC%%%"):
                wfd.write("Files: *\n")
                wfd.write("Copyright: %s\n" % copyrights)
                wfd.write("License: LGPL-2.1+\n")
                wfd.write("\n")
            else:
                wfd.write(line)


directory = os.path.join(os.getcwd(), "debian")
update_debian_control(directory)
update_debian_copyright(directory)
