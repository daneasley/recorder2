#!/usr/bin/python
#
print "-----------------------------------------------------------------------"
print "selector                                                          0.0.1"
print "-----------------------------------------------------------------------"
print 
print "a simple interface for selecting cuts, written with python, tk, & ecasound"
print
print "usage:"
print "    ./selector [config file]"
print "    if no config file is specified, program will look for 'cutrecorder.config'"
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
import ConfigParser                 # load configuration file
import time                         # display time in something other than floating point seconds
from pyeca import *                 # load ecasound for recording
import threading                    # run audio procedures in separate thread, so that gui remains responsive during recording
from threading import *             # (this or the previous line likely redundant)
from subprocess import *            # run system commands

# define Application class
#----------------------------------------------------------------------
class App:

    # This code executes on application startup
    #----------------------------------------------------------------------
    def __init__(self):

        # main window
        root = tk.Tk()      # root is the GUI object.  it must be specified before the variables, as some displayed variables use Tk's StringVar function

        #----------------------------------------------------------------------
        # SET VARIABLES
        #----------------------------------------------------------------------

        # GLOBALS!

        # general variables
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
        temporary_file = "./holymackerel.wav"

        global cut_directory
        cut_directory = "./"

        global cut_filename
        cut_filename = tk.StringVar()
        cut_filename = "foobar.wav"

        global cut_number
        cut_number = "000001"

        global cut_filepath
        cut_filepath = cut_directory + cut_filename

        global cut_duration
        cut_duration = 60.0

        global calculated_time
        calculated_time = 60.0

        global cut_title
        cut_title = "The Origin of Consciousness in the Breakdown of the Bicameral Mind"

        # parse command line arguments
        if len(sys.argv) > 1:
            configuration_file = sys.argv[1]
        else:
            configuration_file = "cutrecorder.config"


        #----------------------------------------------------------------------
        # IMPORT SETTINGS FROM CONFIGURATION FILE
        #----------------------------------------------------------------------

        print "Importing Settings from", configuration_file

        # read file
        config = ConfigParser.ConfigParser()
        config
        config.read(configuration_file)

        # method for getting stuff
        def configsectionmap(section):
            dict1 = {}
            options = config.options(section)
            for option in options:
                try:
                    dict1[option] = config.get(section, option)
                    if dict1[option] == -1:
                        DebugPrint("skip: %s" % option)
                except:
                    print("exception on %s!" % option)
            return dict1

        # get general settings
        root.title (configsectionmap("Settings")['configuration_name'])
        temporary_file = configsectionmap("Settings")['temporary_file']
        cut_directory = configsectionmap("Settings")['destination']

        # (individual cut / label information is grabbed by GUI selection button code)


        #----------------------------------------------------------------------
        # SET GUI ELEMENTS
        #----------------------------------------------------------------------

        root.geometry("1278x1000+0+0")
        root.configure(background="black")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        root.title("Recorder")

        # list frame (left half of window)
        #----------------------------------------------------------------------
        listframe = tk.Frame(root)

        tk.Grid.rowconfigure(root, 0, weight=1)
        tk.Grid.columnconfigure(root, 0, weight=1)

        listframe.grid(row=0, column=0, sticky='')
        listframe.configure(background="black")

        # populate cut selection buttons
        #----------------------------------------------------------------------
        filename = tk.StringVar()
        filename.set("foobar.wav") # initialize

        r = 0
        for cut in config.sections():
            if cut != "Settings":
                holder = ""
                title = configsectionmap(cut)['title']
                filename = configsectionmap(cut)['filename']
                if filename != "label":
                    number = configsectionmap(cut)['cutnumber']
                    duration = float(configsectionmap(cut)['duration'])
                    formatted_duration = '%02d:%02d' % (duration / 60, duration % 60)
                    button_text = title + "    [ length: " + formatted_duration + " ] "
                    select_button = tk.Radiobutton(listframe, text=button_text, variable=holder, value=filename, indicatoron=0, width="70", command=partial(self.set_cut_filepath, filename, number, duration, title), font=('times', 24, 'bold'), foreground='black', background='white', activebackground='goldenrod', selectcolor='tomato')
                    select_button.grid(row=r, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky='nsew')
                else:
                    label_text = title
                    label = tk.Label(listframe, font=('times', 18, 'bold'), text=label_text, foreground='white', background='black')
                    label.grid(row=r, column=0, ipadx=5, ipady=5, padx=7, pady=5, sticky='nsew')
                r = r + 1

        # reset filename so user is forced to select a cut
        filename = "foobar.wav"

        #----------------------------------------------------------------------
        # Begin Main GUI Loop
        #----------------------------------------------------------------------

        root.mainloop()

    #----------------------------------------------------------------------
    # SELECT CUT
    #
    # When a selection button is pushed, it calls this code to put the selected cut's filename in the variable.
    #----------------------------------------------------------------------
    def set_cut_filepath(self, filename, number, duration, title):
        global cut_directory
        global cut_filename
        global cut_number
        global cut_filepath
        global cut_duration
        global cut_title
        if filename != "label":
            cut_filename = filename
            cut_number = number
            cut_filepath = cut_directory + cut_number + "_" + cut_filename
            cut_duration = str(duration)
            cut_title = title
            status_text.set('Ready to record.')
            commandstring = "./recorder2.py " + cut_directory + " " + cut_filename + " " + cut_number + " " + cut_duration + ' "' + cut_title + '"'
            print commandstring
            subprocess.Popen("jackd -R -S -dalsa -r44100 -p1024 -n3 -Phw:USB,0 -Chw:USB,0", shell=True)
            time.sleep(1)
            subprocess.call(commandstring, shell=True)
            subprocess.call("killall jackd", shell=True)
        else:
            return

# Instantiate!
#----------------------------------------------------------------------

Main = App()

