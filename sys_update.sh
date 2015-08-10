#!/bin/bash

# Daniel Fernandez Rodriguez <gmail.com daferoes>

# Updates the system and removes old cached packages on a pacman
# package manager based system (ArchLinux, Manjaro, etc.)

pacman -Syu --noconfirm > /dev/null
pacman -Sc  --noconfirm > /dev/null
