
# Embedded Operating System for i.MX6UL (EOS)

This project contains the source, build scripts, and configurations for a lightweight and secure embedded operating system targeting the NXP i.MX6UL platform.

##  Directory Structure

 - .
 - ├── bootloader/ # U-Boot source and prebuilt binaries
 - ├── kernel/ # Linux kernel source and kernel defconfig
 - ├── rootfs/ # Root filesystem (extracted and compressed)
 - ├── README.md # This file


##  Build Instructions

### Prerequisites

- Ubuntu 22.04 LTS or similar
- Cross-compiler for ARM (e.g., `arm-linux-gnueabihf-`)
- `u-boot-tools` for `mkimage`
- `make`, `gcc`, `tar`, etc.

Install dependencies:
 - sudo apt install build-essential u-boot-tools gcc-arm-linux-gnueabihf make libncurses-dev libssl-dev

## Build Steps

        To build and generate all output boot files:
        ./build.sh
        This script will:
         - Copy uImage, DTB, and U-Boot image to outputs/
         - Apply kernel and U-Boot defconfigs
         - Generate boot.scr from boot.txt using mkimage

## Output Files
        After a successful build, the outputs/ directory will contain:
         - uImage – Linux kernel image
         - imx6ul-14x14-evk.dtb – Device tree blob
         - u-boot-with-spl.imx – Bootloader binary
         - boot.scr – Boot script for U-Boot
         - boot.txt – Source script for boot.scr

## Configuration Files
configs/kernel_defconfig
Copied to kernel/linux-imx/arch/arm/configs/imx_v6_v7_defconfig

configs/uboot_defconfig
Copied to bootloader/u-boot/configs/mx6ul_14x14_evk_defconfig

## Flashing Instructions
 Flashing via SD Card:
 Use dd to write images to SD card:
 sudo dd if=u-boot-with-spl.imx of=/dev/sdX bs=512 seek=2 conv=fsync && sync

 Then copy uImage, .dtb, and boot.scr to the /BOOT partition.

## Security Features
 - The image is designed with support for:
 - CAAM (Cryptographic Accelerator and Assurance Module)
 - Trusted Keys framework
 - Optional AppArmor/SELinux (manual integration)

## Helpful Scripts
 scripts/backup.sh – Backup your existing SD card to image files
 build.sh – Automate image generation and boot setup

## Maintainers
  - Nikhil Yadav - Project Engineer – CDAC
  - Maroti Shinde  - Project Engineer - CDAC
  - Ajay Bajpai - Project Associate - CDAC
  - T V Madhavan - Project Associate - CDAC

## License
 This project is released under the MIT License.
 You are free to modify, distribute, and use for commercial or personal projects.

## Version
 EOS v1.0 – For NXP i.MX6UL based boards

