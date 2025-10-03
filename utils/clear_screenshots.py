import os
import glob
import time

SCREENSHOTS_DIR = 'screenshots'
AGE_SECONDS = 0

def clear_screenshots():
    if not os.path.exists(SCREENSHOTS_DIR):
        print(f'Папка {SCREENSHOTS_DIR} не существует.')
        return
    now = time.time()
    files = glob.glob(os.path.join(SCREENSHOTS_DIR, '*'))
    count = 0
    for f in files:
        if os.path.isfile(f):
            mtime = os.path.getmtime(f)
            if now - mtime > AGE_SECONDS:
                os.remove(f)
                count += 1
    print(f'Удалено {count} файлов старше 1 дня из папки {SCREENSHOTS_DIR}.')

if __name__ == '__main__':
    clear_screenshots() 