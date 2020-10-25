
==========
Time Lapse
==========

A simple wrapper around screencapture to create a time lapse of the contents of a window.

Usage
=====

usage: timelapse.py [-h] [-w WINDOW_ID] [-i INTERVAL] [-o OUTPUT]
                    [-c MAX_CAPTURE] [-s STOP_MARKER] [-v]

Take a time lapse of an application window using 'screencapture' (macOS only).
To stop capturing enter the 'q' key to quit.

optional arguments:
  -h, --help            show this help message and exit
  -w WINDOW_ID, --window-id WINDOW_ID
                        Id of the window to capture.
  -i INTERVAL, --interval INTERVAL
                        Interval in seconds between captures [default is 5].
  -o OUTPUT, --output OUTPUT
                        The output directory for the captured images.
  -c MAX_CAPTURE, --max-capture MAX_CAPTURE
                        Max capture time in seconds [default is 3600].
  -s STOP_MARKER, --stop-marker STOP_MARKER
                        Key to enter to stop program [default key is 'q'].
  -v, --verbose         Add debugging output.
