import dlal

import atexit
from datetime import datetime
from pathlib import Path
import pprint
import sqlite3
import threading
import time
import weakref

def timestamp():
    return datetime.now().astimezone().isoformat(' ', 'seconds')

class MonitorSys(dlal.subsystem.Subsystem):
    def init(self, name=None):
        dlal.subsystem.Subsystem.init(self,
            {
                'audio': ('audio', [], {'driver': True, 'run_size': 4096, 'mic': True}),
                'afw': ('afw', [], {'context_duration': 5}),
                'stft': 'stft',
                'monitor': (
                    'monitor',
                    [],
                    {
                        'format': (
                            'write_start',
                            ['%.wav', 5],
                            {},
                        ),
                        'known_category_cmd_rate': 0.01,
                    },
                ),
            },
            name=name,
        )
        dlal.connect(
            [self.audio, '+>', self.afw],
            self.stft,
            [self.monitor, '+>', self.afw],
        )

    def start(self):
        self.audio.start()
        atexit.register(lambda: self.audio.stop())

    def start_db(self):
        self.db_thread_quit = False
        weak_self = weakref.proxy(self)
        def f():
            need_schema = not Path('monitor.db').exists()
            con = sqlite3.connect('monitor.db')
            if need_schema: con.executescript('''
                CREATE TABLE categories(time REAL, categories TEXT);
                CREATE INDEX categories_time ON categories(time);
                CREATE TABLE lifeline(time REAL);
                CREATE INDEX lineline_time ON lifeline(time);
            ''')
            con.execute(f'''INSERT INTO lifeline VALUES ({time.time()})''')
            con.commit()
            alive_h = int(time.time()) // 3600
            while True:
                categories = ' '.join(
                    i for i in weak_self.monitor.take_recent_categories()
                    if not i.startswith('unknown')
                )
                if categories:
                    con.execute(f'''INSERT INTO categories VALUES ({time.time()}, '{categories}')''')
                    con.commit()
                m = int(time.time()) // 60
                while m == int(time.time()) // 60:
                    time.sleep(1)
                    if self.db_thread_quit: return
                h = int(time.time()) // 3600
                if h != alive_h:
                    con.execute(f'''INSERT INTO lifeline VALUES ({time.time()})''')
                    con.commit()
                    alive_h = h
        self.db_thread = threading.Thread(target=f)
        self.db_thread.daemon = True
        self.db_thread.start()

    def stop_db(self):
        self.db_thread_quit = True
        self.db_thread.join()

    def print_category_changes(self):
        category = None
        while True:
            cat = self.monitor.category_detected()
            if category != cat:
                category = cat
                print(timestamp(), category)
            time.sleep(1)

    def print_category_distances(self):
        while True:
            pprint.pprint(self.monitor.category_distances())
            time.sleep(1)
