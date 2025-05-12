import multiprocessing

from potato_checker import PotatoChecker
from potato_gui import PotatoGui

if __name__ == '__main__':
    message_q = multiprocessing.Queue()
    message_q.cancel_join_thread()

    checker = PotatoChecker(message_q)
    checker_process = multiprocessing.Process(target=checker.mainloop)
    gui = PotatoGui(message_q)

    checker_process.start()
    gui.mainloop()

    checker_process.kill()
