import dlal

import atexit
from datetime import datetime
import json
from pathlib import Path
import pprint
import sqlite3
import threading
import time
import weakref

def timestamp():
    return datetime.now().astimezone().isoformat(' ', 'seconds')

class MonitorSys(dlal.subsystem.Subsystem):
    def init(self, *, name=None, driver=True):
        dlal.subsystem.Subsystem.init(self,
            {
                'audio': ('audio', [], {'driver': driver, 'run_size': 4096, 'mic': True}),
                'comm': 'comm',
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
                    i for i in weak_self.monitor.category_take_recent()
                    if not i.startswith('unknown')
                )
                if categories:
                    con.execute(f'''INSERT INTO categories VALUES ({time.time()}, '{categories}')''')
                    con.commit()
                q = int(time.time()) // (60 * 15)
                while q == int(time.time()) // (60 * 15):
                    time.sleep(1)
                h = int(time.time()) // 3600
                if h != alive_h:
                    con.execute(f'''INSERT INTO lifeline VALUES ({time.time()})''')
                    con.commit()
                    alive_h = h
        self.db_thread = threading.Thread(target=f)
        self.db_thread.daemon = True
        self.db_thread.start()

    def start_cleaner(self):
        def f():
            while True:
                now = time.time()
                for path in Path('.').glob('*.wav'):
                    if now - path.stat().st_ctime > 15 * 24 * 3600:
                        path.unlink()
                time.sleep(600)
        self.cleaner_thread = threading.Thread(target=f)
        self.cleaner_thread.daemon = True
        self.cleaner_thread.start()

    def start_server(self):
        dlal.serve(
            home_page='systems/monitor/index.html',
            store={'monitor_sys': self},
        )

    def start_all(self):
        self.start()
        self.start_db()
        self.start_cleaner()
        self.start_server()

    def save(self, path='monitor.json'):
        j = self.monitor.to_json()
        with open(path, 'w') as f: json.dump(j, f, indent=2)

    def load(self, path='monitor.json'):
        with open(path) as f: j = json.load(f)
        self.monitor.from_json(j)

    def db_categories(self, since, until):
        since = datetime.fromisoformat(since).timestamp()
        until = datetime.fromisoformat(until).timestamp()
        con = sqlite3.connect('monitor.db')
        cur = con.execute(f'''
            SELECT time, categories
            FROM categories
            WHERE time BETWEEN {since} and {until}
            ORDER BY time
        ''')
        return cur.fetchall()

    def list_wavs_for_category(self, name):
        return [str(i) for i in Path('.').glob(f'*-{name}.wav')]

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
