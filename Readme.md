# Micropython framework

This is a collection of snippets and tools to implement Micropython for ESP32 boards. The idea is to implement emulators and relays with this technology.

In general there exists a bash script **./mp.sh** on the top level, which could be easy used for the install, compile and deploy activity.

## install

Clone the repo and run ./mp.sh - You will see help instructions

## compile

Due to the general lack of resources on embedded systems, a compilation is carried out for a large part of the files: py -> mpy, html -> html.gz

## deploy 

In this step, all files required via ./src/<project>/require.txt are linked from the ./lib/ directory to the ./src/<project> folder, then a connection to the device is made and which files are compared are newer, these will then be compiled. All of this happens in a ./build/ directory. This can be deleted at any time (if something gets stuck somewhere). Backups are created and the files to be deployed are compiled in ./build/output/<project>. These files are then copied to the embedded device. You can observe this process in the console. Information on the elapsed time and the resources used is also provided. In the python command line you can then perform a soft reboot with Ctrl-D and see in the console how the system is booted on the embedded device.
