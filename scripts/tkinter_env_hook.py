import os
import sys


def _set_tcl_tk_env():
    """Ensure Tcl/Tk library paths are set at runtime."""
    if hasattr(sys, 'frozen'):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    tcl_dir = os.path.join(base_dir, 'tcl')
    tk_dir = os.path.join(base_dir, 'tk')

    if os.path.isdir(tcl_dir):
        os.environ.setdefault('TCL_LIBRARY', tcl_dir)
    if os.path.isdir(tk_dir):
        os.environ.setdefault('TK_LIBRARY', tk_dir)


_set_tcl_tk_env()
