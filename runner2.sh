#!/bin/bash

# Cut Recorder wrapper script

# stupid hack to make sure we're in the working directory.  autostart file should do this but doesn't.
    cd ~/cutrecorder

# wait 15 seconds for system to finish booting
    echo Waiting 15 seconds.
    sleep 15s


# Logging
    echo Configuring Logging System.
    # delete log file
        rm ~/cutrecorder/cutrecorder.log
    # set log file variable                                             ***********************************
        export ECASOUND_LOGFILE=~/cutrecorder/cutrecorder.log
    # run following code in separate (minimized) terminal window                fix these!!!
        #watch -n 1 -d tail --lines 40 ~/cutrecorder.log                ***********************************

# Run Cut Recorder in infinite loop (performing kludgy cleanup on other applications' window size/locations each iteration)
    echo Beginning recorder loop.
    while true; do
        # move/resize Web Browser window to all of second monitor
        wmctrl -r Iceweasel -e 0,1281,0,1278,1000
        # run cutrecorder with different configuration file based on day
        case "$(date +%a)" in 
            Mon) 
                ./selector.py monday.config
                ;;
            Tue|Wed|Thu)
                ./selector.py other.config
                ;;
            Fri)
                ./selector.py friday.config
                ;;
            Sat|Sun) 
                ./selector.py other.config
                ;;
        esac
        sleep 2s
    done

echo Terminating.

