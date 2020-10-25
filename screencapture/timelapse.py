#!/usr/bin/env python

import os
import sys
import time
import argparse

from queue import Queue, Empty
from threading import Thread
from subprocess import Popen


def process_argument():
    parser = argparse.ArgumentParser(description="Take a time lapse of an application window using 'screencapture'"
                                                 " (macOS only). To stop capturing enter the 'q' key to quit.")
    parser.add_argument("-w", "--window-id",
                        help="Id of the window to capture.")
    parser.add_argument("-i", "--interval", type=int, default=5,
                        help="Interval in seconds between captures [default is 5].")
    parser.add_argument("-o", "--output",
                        help="The output directory for the captured images.")
    parser.add_argument("-c", "--max-capture", type=int, default=3600,
                        help="Max capture time in seconds [default is 3600].")
    parser.add_argument("-s", "--stop-marker", default='q',
                        help="Key to enter to stop program [default key is 'q'].")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Add debugging output.")

    return parser


def capture_screen(q, options):
    count = 0
    finished = False
    while not finished:

        try:
            item = q.get(block=True, timeout=options["interval"])
            q.task_done()
            if item == "quit":
                print('quitting')
                finished = True

        except Empty:
            count += 1
            Popen(['screencapture', '-x', '-l', options["window_id"],
                   os.path.join(options["output"], f'screenshot-{count:05}.png')])


def input_watcher(q, options):
    finished = False
    while not finished:
        key = input("")
        if key == options["stop_marker"]:
            q.put("quit")
            finished = True


def timeout_watcher(q, options):
    finished = False
    start_epoch = time.time()
    while not finished:
        time.sleep(0.25)
        if (time.time() - start_epoch) > options["max_capture"]:
            q.put("quit")
            finished = True


def valid_args(args):
    if args.output is None or args.interval is None or args.window_id is None:
        return False

    if not os.path.isdir(args.output):
        return False

    return True


def main():
    parser = process_argument()
    args = parser.parse_args()

    if args.verbose:
        print('Interval: ' + (args.interval if args.interval is not None else 'not set'))
        print('Output: ' + (args.output if args.output is not None else 'not set'))
        print('Window id: ' + (args.window_id if args.window_id is not None else 'not set'))

    if not valid_args(args):
        return 1

    q = Queue()
    options = {'max_capture': args.max_capture, 'output': args.output,
               'window_id': args.window_id, 'interval': args.interval,
               'stop_marker': args.stop_marker}
    capture_thread = Thread(name="CaptureScreenThread",
                            target=capture_screen,
                            args=(q, options, ))
    input_thread = Thread(name="InputThread",
                          target=input_watcher,
                          daemon=True,
                          args=(q, options, ))
    timeout_thread = Thread(name="TimeoutThread",
                            target=timeout_watcher,
                            daemon=True,
                            args=(q, options, ))
    capture_thread.start()
    input_thread.start()
    timeout_thread.start()

    q.join()
    # input_thread.join()
    capture_thread.join()

    return 0


if __name__ == "__main__":
    sys.exit(main())
