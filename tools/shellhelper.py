from __future__ import print_function
import os
import platform
import sys
import subprocess
import time

# global flag indicating whether we are on linux virtual console
is_linux_tty = (platform.system() == 'Linux' and os.isatty(1))

# total shell commands' execution time outside Python interpreter
external_execution_time = 0.0


def get_external_execution_time():
    global external_execution_time
    return external_execution_time


def get_pipe_output(cmds, quiet=False):
    """
    Helper function to launch shell commands. Additionally measures the execution time
    :param cmds: list with a shall command and its args
    :param quiet: verbosity flag
    :return: commands' output
    """
    global external_execution_time
    global is_linux_tty
    start = time.time()

    if not quiet and is_linux_tty:
        print('>> ' + ' | '.join(cmds), end=' ')
        sys.stdout.flush()
    p = subprocess.Popen(cmds[0], stdout=subprocess.PIPE, shell=True)
    processes = [p]
    for x in cmds[1:]:
        p = subprocess.Popen(x, stdin=p.stdout, stdout=subprocess.PIPE, shell=True)
        processes.append(p)
    output = p.communicate()[0]
    for p in processes:
        p.wait()
    end = time.time()
    if not quiet:
        if is_linux_tty:
            print('\r', end=' ')
        print('[%.5f] >> %s' % (end - start, ' | '.join(cmds)))
    external_execution_time += (end - start)
    return output.rstrip('\n')
