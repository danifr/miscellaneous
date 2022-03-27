#!/bin/bash

## Daniel Fernandez Rodriguez <gmail.com daferoes>

ALARM_URL='http://os.archlinuxarm.org/os/ArchLinuxARM-rpi-armv7-latest.tar.gz'
ALARM_CHECKSUM_URL='http://os.archlinuxarm.org/os/ArchLinuxARM-rpi-armv7-latest.tar.gz.md5'

verify_checksum() {
    ALARM_PATH=$1
    REMOTE_ALARM_CHECKSUM=$(curl -L $ALARM_CHECKSUM_URL | cut -f1 -d ' ' | xargs)
    LOCAL_ALARM_CHECKSUM=$(md5sum $ALARM_PATH | cut -f1 -d ' ' | xargs)
    echo "[INFO] Verifying $ALARM_PATH checksum ($LOCAL_ALARM_CHECKSUM vs $REMOTE_ALARM_CHECKSUM)..."
    if [[ "$REMOTE_ALARM_CHECKSUM" == "$LOCAL_ALARM_CHECKSUM" ]]; then
      return 0
    else
      return 1
    fi
}

download_latest_alarm(){
   ALARM_PATH=$1
   echo "[INFO] Downloading latest version of ArchLinuxARM from $ALARM_URL"
   curl -L --output $ALARM_PATH $ALARM_URL
}

if [[ $UID -ne 0 ]]; then
  echo '[ERROR] You need to run this program as root or via sudo... Exiting'
  exit 1
fi

echo '+***********************************************************+'
echo '*                                                           *'
echo '*  Welcome! This program will automate the installation of  *'
echo '*        ArchLinuxARM RP2 on your microSD card.             *'
echo '*                                                           *'
echo '+***********************************************************+'

read -r -p "Please enter your sdcard device name [mmcblk0]: " SDCARD
if [[ -n $SDCARD ]]; then
  if [[ $SDCARD != /dev/* ]]; then
    SDCARD="/dev/$SDCARD"
  fi
else
  SDCARD="/dev/mmcblk0"
fi

test -b $SDCARD
if [[ $? -eq 0 ]]; then
  read -r -p "This program will FORMAT and INSTALL ArchLinuxARM on $SDCARD. Are you sure you want to continue?(y/n): " CONTINUE
  if [[ ${CONTINUE,,} == 'y' ]]; then
    #umount sdcard if mounted
    mounted=$(mount)
    if [[ $mounted == *$SDCARD* ]]; then
      echo '[INFO] Unmounting SD card...'
      umount $(echo "$mounted" | grep $SDCARD | awk '{print $3}')
      if [[ $? -ne 0 ]]; then
        echo '[ERROR] Impossible to umount SD card... Exiting'
        exit 1
      fi
    fi

    echo [INFO] Creating partitions on $SDCARD...
    (echo o; echo n; echo p; echo 1; echo; echo +200M; echo t; echo c; echo n; echo p; echo 2; echo; echo; echo w) | fdisk $SDCARD
    echo [INFO] Formating partitions...
    mkfs.vfat "$SDCARD"p1
    mkfs.ext4 -F "$SDCARD"p2

    RPI_BOOT_DIR='/tmp/raspberrypi/boot'
    RPI_ROOT_DIR='/tmp/raspberrypi/root'
    echo [INFO] Creating temporary mount directories...
    mkdir -p $RPI_BOOT_DIR $RPI_ROOT_DIR
    echo '[INFO] Mounting...'
    mount "$SDCARD"p1 $RPI_BOOT_DIR
    mount "$SDCARD"p2 $RPI_ROOT_DIR

    read -r -p "Enter where to store ArchLinuxARM release [/tmp/ArchLinuxARM-rpi-2-latest.tar.gz]: " ALARM_PATH
    if [[ -z "$ALARM_PATH" ]]; then
      ALARM_PATH=/tmp/ArchLinuxARM-rpi-2-latest.tar.gz
    fi

    if [[ -f "$ALARM_PATH" ]]; then
      if ! verify_checksum $ALARM_PATH; then
        download_latest_alarm $ALARM_PATH
      fi
    else
      download_latest_alarm $ALARM_PATH
    fi

    if ! verify_checksum $ALARM_PATH; then
      echo '[ERROR] Checksum does not match... Exiting'
      exit 1
    fi

    echo "[INFO] Extracting files into $RPI_ROOT_DIR..."
    bsdtar -xpf $ALARM_PATH -C $RPI_ROOT_DIR
    echo '[INFO] Syncing... (this might take a while)'
    sync

    echo "[INFO] Copying boot into $RPI_BOOT_DIR"
    mv "$RPI_ROOT_DIR"/boot/* $RPI_BOOT_DIR
    echo "[INFO] Unmounting..."
    umount $RPI_BOOT_DIR $RPI_ROOT_DIR
    rm -rf $RPI_BOOT_DIR
    rm -rf $RPI_ROOT_DIR
    echo "[INFO] Everything looks good! Insert the sdcard in you RaspberryPi and have fun!"
    echo "
Use the serial console or SSH to the IP address given to the board by your router.

    Login as the default user alarm with the password alarm.
    The default root password is root.

Initialize the pacman keyring and populate the Arch Linux ARM package signing keys:

pacman-key --init
pacman-key --populate archlinuxarm


"

  else
    echo "[INFO] Exiting. Have a good day!"
    echo 0
  fi

else
  echo "[ERROR] $SDCARD not found as valid block device :( Exiting..."
  exit 1
fi
