#!/usr/bin/python
#
print "-----------------------------------------------------------------------"
print "recorder2                                                         0.0.1"
print "-----------------------------------------------------------------------"
print 
print "a simple interface for recording cuts, written with python, tk, & ecasound"
print
print "usage:"
print "    ./recorder2 directory filename cutnumber duration title"
print

# system requirements:
#
#       jack audio connection kit   (low-level audio system)
#       ecasound                    (intermediary system for recording)
#       python-ecasound             (python library to interact with ecasound)
#       python-tk                   (python library for GUI)
#       sox                         (for post-processing)
#

# import classes and procedures
import sys, os                      # parse command line arguments
import Tkinter as tk                # GUI library
import tkMessageBox                 # popup windows
from functools import partial       # advanced function calling (don't yet understand: using global variables instead (bad?! philosophy?!))
import time                         # display time in something other than floating point seconds
from pyeca import *                 # load ecasound for recording
import threading                    # run audio procedures in separate thread, so that gui remains responsive during recording
from threading import *             # (this or the previous line likely redundant)
from subprocess import *            # run system commands

# define Recorder class, using pyeca (python-ecasound bridge, hardcoded below for JACK on linux.  google ecasound-iam for rosettastone)

class Recorder(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.running = False
        self.horseholder = False
        self.e = ECA_CONTROL_INTERFACE(0)
        self.e.command("int-set-log-history-length 1024")
        self.e.command("int-log-history")
        self.e.command("cs-add rec_chainsetup")
        self.e.command("c-add 1st_chain")
        self.e.command('cs-set-audio-format 16,2,44100')
        self.e.command("cs-option -G:jack,cutrecorder,notransport")
        self.e.command("ai-add jack,system")
        print "Recording System Initialized."

    def start_recorder(self):
        if self.running == False:
            call(["rm", temporary_file + cut_filename])
            time.sleep(0.5)
            fileconnector = "ao-add " + temporary_file + cut_filename
            self.e.command(fileconnector)
            self.e.command("cs-connect")
            self.e.command("start")
            print "Recording Started."
            status_text.set('RECORDING ' + cut_title)
            record_button_label.set('pause')
            self.running = True
            self.start()
        else:
            pass

    def stop_recorder(self):
        self.horseholder = True
        time.sleep(0.5)
        status_text.set('Saving. Please wait.')
        self.e.command("stop")
        print "Recording Stopped."
        time.sleep(2)
        status_text.set('Making file monaural.')
        call(["cp", temporary_file + cut_filename, "temp-toconvert.pcm"])
        call("sox -t raw -b 16 -e signed-integer -r 44100 -c 2 temp-toconvert.pcm " + temporary_file + cut_filename + " channels 1", shell = True)
        status_text.set('Copying to final destination.')
        call(["cp", temporary_file + cut_filename, cut_filepath])
        status_text.set('Recording Saved.')
        print "Recording Saved to ", cut_filepath
        tkMessageBox.showinfo("Recording Saved", "Recording Finished and Saved.")
        os._exit(1)

    def cancel_recorder(self):
        if self.e.command("engine-status") == "running":
            self.pause_recorder()
        response = tkMessageBox.askquestion("Cancel Recording", "Are you sure you want to cancel the recording? (It's currently paused.)", icon='warning')
        if response == 'yes':
            self.e.command("cs-disconnect")
            status_text.set('Cancelled.')
            print "Recording Cancelled."
            os._exit(1)
        else:
            return

    def pause_recorder(self):
        self.horseholder = True
        time.sleep(0.5)
        if self.e.command("engine-status") == "stopped":
            self.e.command("start")
            time.sleep(0.5)
            self.horseholder = False
            status_text.set('RECORDING ' + cut_title)
            record_button_label.set('pause')
            print "Recording Resumed."
        else:
            self.e.command("stop")
            time.sleep(0.5)
            status_text.set('Paused. (' + cut_title + ')')
            record_button_label.set('resume')
            print "Recording Paused."

    def run(self):
        while self.running:
            time.sleep(0.5)
            if self.horseholder != True:
                self.e.command("cs-get-position")
                current_position = self.e.last_float()
                calculated_time = cut_duration - current_position
                formatted_time = '  %02d:%02d  ' % (calculated_time / 60, calculated_time % 60)
                displayed_time.set(formatted_time)
                if current_position >= cut_duration:
                    print "Timer ran to zero."
                    self.running = False
                    displayed_time.set('  00:00  ')
        self.stop_recorder()
        return

# define Application class
#----------------------------------------------------------------------
class App:

    # This code executes on application startup
    #----------------------------------------------------------------------
    def __init__(self):

        # main window
        root = tk.Tk() # root is the GUI object, specified before the variables, as some displayed variables use Tk's StringVar function

        # SET VARIABLES

        # User Interface variables
        global displayed_time
        displayed_time = tk.StringVar()
        displayed_time.set('  00:00  ')

        global status_text
        status_text = tk.StringVar()
        status_text.set('Select your recording.')

        global record_button_label
        record_button_label = tk.StringVar()
        record_button_label.set('record')

        global stop_button_label
        stop_button_label = tk.StringVar()
        stop_button_label.set('stop and save')

        global cancel_button_label
        cancel_button_label = tk.StringVar()
        cancel_button_label.set('cancel')

        # working cut variables

        global temporary_file
        temporary_file = "./cutrecorder-tempfile.wav"
        global calculated_time
        calculated_time = 60.0

        global cut_directory
        global cut_filename
        global cut_number
        global cut_filepath
        global cut_duration
        global cut_title

        # parse command line arguments

        cut_directory = sys.argv[1]
        cut_filename = sys.argv[2]
        cut_number = sys.argv[3]
        cut_filepath = cut_directory + cut_number + "_" + cut_filename
        cut_duration = float(sys.argv[4])
        cut_title = sys.argv[5]

        status_text.set('Ready to record ' + cut_title + '.')
        print "Ready to record", cut_title, "to be saved as", cut_filepath

        #----------------------------------------------------------------------
        # SET GUI ELEMENTS
        #----------------------------------------------------------------------

        root.geometry("1200x1024+0+0")
        root.configure(background="black")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        root.title("Recorder")

        # buttons
        #----------------------------------------------------------------------

        controlframe = tk.Frame(root)
        controlframe.grid(row=0, column=0, sticky='')
        controlframe.configure(background="black")

        clock = tk.Label(controlframe, textvariable = displayed_time, font=('times', 96, 'bold'), foreground='goldenrod', background='black')
        clock.grid(columnspan=1, row=0, column=0, ipadx=30, ipady=30, padx=10, pady=10, sticky='')

        status = tk.Label(controlframe, textvariable = status_text, font=('times', 24, 'bold'), foreground='black', background='goldenrod')
        status.grid(columnspan=1, row=1, column=0, ipadx=30, ipady=30, padx=10, pady=10, sticky='')

        record_button = tk.Button(controlframe, textvariable = record_button_label, font=('times', 48, 'bold'), foreground='red', background='white', width="15", command=partial(self.start_recording))
        record_button.grid(row=2, column=0, ipadx=10, ipady=10, padx=5, pady=12, sticky='')

        stop_button = tk.Button(controlframe, textvariable = stop_button_label, font=('times', 48, 'bold'), foreground='blue', background='white', width="15", command=partial(self.stop_recording))
        stop_button.grid(row=3, column=0, ipadx=10, ipady=10, padx=5, pady=12, sticky='')

        cancel_button = tk.Button(controlframe, textvariable = cancel_button_label, font=('times', 48, 'bold'), foreground='goldenrod', background='white', width="15", command=partial(self.cancel_recording))
        cancel_button.grid(row=4, column=0, ipadx=10, ipady=10, padx=5, pady=12, sticky='')

        print

        #----------------------------------------------------------------------
        # Begin Main GUI Loop
        #----------------------------------------------------------------------

        root.mainloop()


    #----------------------------------------------------------------------
    # START RECORDING
    #----------------------------------------------------------------------
    def start_recording(self):
        # Check if a file has been selected; if not, alert user; otherwise, call the start_recorder function of deck
        if deck.running == True:
            deck.pause_recorder()
        else:
            deck.start_recorder()

    def stop_recording(self):
        print "Stop Button Pressed."
        deck.horseholder = True
        deck.running = False

    def cancel_recording(self):
        deck.cancel_recorder()


# Instantiate!
#----------------------------------------------------------------------

deck = Recorder()
Main = App()

