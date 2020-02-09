# miscellaneous, pretty useful stuff (or not)

This is intended to serve as a personal repo where I keep some of the code I wrote to make my life easier.

If you think you can also profit from it, just go ahead and start using it! :)

## What will I find in here?

### [Am I home?](https://github.com/danifr/miscellaneous/tree/devel/amihome)

This program will check if a set of already declared IPs are pingable through the network.

Use it with [motion](https://motion-project.github.io/) (original [code](http://www.lavrsen.dk/foswiki/bin/view/Motion/WebHome)) and the [RaspberryPi Camera Module](https://www.raspberrypi.org/products/camera-module-v2/) to create your own home-made surveillance system.

### [alarm_install](https://github.com/danifr/miscellaneous/blob/devel/alarm_install.sh)

This is a bash script for installing archlinux ARM on a microSD.

It automates all the installation process; downloads the latest image, formats the microSD, creates partitions, etc.

After running it, you just need to insert the sdcard in you RaspberryPi2 and have fun!

### [sys_update](https://github.com/danifr/miscellaneous/blob/devel/sys_update.sh)

Simplest script ever to keep your archlinux system up-to-date and tidy at the same time.

Add it as scheduled systemd unit to run it automatically once per day or week.

### [openafs_update.sh](https://github.com/danifr/miscellaneous/blob/devel/CERN_OpenAFS/openafs_update.sh)

Bash script to fully automate installation and configuration of OpenAFS.
Tested succesfully on Fedora 30, Centos 7/7.X and RHEL7. Please open an issue if it does not work with newer OS releases
