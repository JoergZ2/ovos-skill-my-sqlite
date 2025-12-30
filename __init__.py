import sys
import os
import time
import sqlite3 as sq
from os.path import dirname, isfile
from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import intent_handler
from ovos_workshop.skills import OVOSSkill
from ovos_bus_client.session import SessionManager

class MySqliteDatabaseAssistant(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.override = True

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(internet_before_load=False,
                                   network_before_load=True,
                                   gui_before_load=False,
                                   requires_internet=False,
                                   requires_network=True,
                                   requires_gui=False,
                                   no_internet_fallback=False,
                                   no_network_fallback=False,
                                   no_gui_fallback=False)

    def initialize(self):
        self.settings_change_callback = self.on_settings_changed
        self.on_settings_changed()
        self.data_dir = self.settings.get('data_dir', None)


    def on_settings_changed(self):
        self.data_dir = self.settings.get('data_dir')
        self.db_file = self.settings.get('db_file')
        LOG.info("Db path and file: " + str(self.data_dir) + ", " + str(self.db_file))

    def check_if_path_and_db_exists(self,db_file=None):
        if db_file == None or db_file == "not set":
            self.speak_dialog('create.database.default')
            user_dir = os.path.expanduser("~")
            data_dir = os.path.join(user_dir, "databases")
            db_file = os.path.join(data_dir,"objects.db")
            if not os.path.isdir(data_dir):
                os.makedirs(data_dir)
            self.settings["db_file"] = db_file
            self.settings["data_dir"] = data_dir
            self.settings.store()
            self.db_file = self.settings.get('db_file', None)
            self.create_database(db_file)
            self.con = sq.connect(self.db_file, check_same_thread=False)
            return True
        else:
            return True

    def create_database(self, db_file):
        try:
            self.con = sq.connect(db_file, check_same_thread=False)
            self.cursor = self.con.cursor()
            sql = """
            CREATE TABLE items (key INTEGER PRIMARY KEY AUTOINCREMENT,t_name TEXT NOT NULL,t_synonym TEXT,t_storage TEXT,t_place TEXT)
            """
            self.cursor.execute(sql)
            self.con.commit()
            LOG.info(f"Database created! Path and file name {db_file}")
        except sq.OperationalError as e:
            LOG.info("Error: " + str(e))
            self.speak_dialog('no_database',{'database': self.db_file})
            pass

    def execute_sql(self, sql, item=None, last_id=None):
        LOG.info("db path: " + str(self.db_path))
        if self.check_if_path_and_db_exists(db_file=self.db_file):
            try:
                self.con = sq.connect(self.db_file, check_same_thread=False)
                self.cursor = self.con.cursor()
                self.cursor.execute(sql)
                self.con.commit()
                if "INSERT" in sql:
                    last_id = self.cursor.lastrowid
                    self.write_lastid(last_id)
                    self.speak_dialog('insert.succesfull', {'item': item})
                if "UPDATE" in sql:
                    self.speak_dialog('update.succesfull',{'last_id': last_id})
            except sq.OperationalError as e:
                LOG.info("Datenbankfehler: " + str(e))
                self.speak_dialog('no_database',{'database': self.db_file})
                return
        else:
            pass
    
    def write_lastid(self, last_id):
        with open('/tmp/joergz2_sqlite_lastid','w') as lastid:
            lastid.write(str(last_id))
            lastid.close()

    def read_lastid(self):
        with open('/tmp/joergz2_sqlite_lastid','r') as lastid:
            last_id = lastid.readline()
            lastid.close()
            return last_id

##Database functions    
    def check_item_names_exact(self, item):
        """Checks if an item exists and returns the ID"""
        sql = """
        SELECT t_name, t_synonym, t_storage, t_place FROM items WHERE t_name LIKE '"""+ '%' + item.lower() + '%'+"""';
        """
        self.execute_sql(sql, item)
        res = self.cursor.fetchall()
        return res
    
    def check_item_names_raw(self, item):
        """Checks if an item exists and returns the ID"""
        sql = """
        SELECT t_name, t_synonym, t_storage, t_place FROM items WHERE t_name LIKE '"""+ '%' + item.lower() + '%'+"""';
        """
        self.execute_sql(sql)
        res = self.cursor.fetchall()
        return res
    

    def check_item_synonyms(self, item):
        """Checks if an item exists and returns the ID"""
        sql = """
        SELECT t_name, t_synonym, t_storage, t_place FROM items WHERE t_synonym LIKE '"""+ '%' + item.lower() + '%'+"""';
        """
        self.execute_sql(sql)
        res = self.cursor.fetchall()
        return res
    
    def insert_new_item(self, item, synonym, storage, place):
        stored_item = self.check_item_names_exact(item)
        item, synonym, storage, place = self.make_lower(item, synonym, storage, place)
        sql = """
            INSERT INTO items (key, t_name, t_synonym, t_storage, t_place) VALUES \
                (NULL, '""" + item +"""', '""" + synonym + """', '""" + storage +"""',\
                 '""" + place +"""');
            """
        self.execute_sql(sql, item=item)
        #else:
            #self.speak_dialog('item.is.stored', {'item': item})

    def insert_single_item(self, item):
        stored_item = self.check_item_names_exact(item)
        sql = """
            INSERT INTO items (key, t_name) VALUES \
                (NULL, '""" + item.lower() +"""');
            """
        self.execute_sql(sql, item)

    def update_last_insert(self, column, value):
        last_id = self.read_lastid()
        sql = """
            UPDATE items set '""" + column + """' = '""" + value + """' where key = '""" + last_id + """';
            """
        self.execute_sql(sql, last_id=last_id)

## Helper functions
#Formatting data tuples to speech
    def make_utterance(self, res, item):
        if len(res) == 0:
            self.speak_dialog('noitem', {'item': item})
        else:
            i = 0
            while i < len(res):
                item = res[i][0]
                storage = res[i][2]
                place = res[i][3]
                self.speak_dialog('item.is.in', {'item': item, 'storage': storage, 'place': place})
                i += 1

    def make_utterance_from_synonym(self, res, item):
        if len(res) == 0:
            self.speak_dialog('noitem', {'item': item})
        else:
            i = 0
            while i < len(res):
                item = res[i][0]
                synonym = res[i][1]
                storage = res[i][2]
                place = res[i][3]
                self.speak_dialog('synonym.is.in', {'item': item, 'synonym': synonym, 'storage': storage, 'place': place})
                time.sleep(1)
                i += 1

    def make_lower(self, item, synonym, storage, place):
        if item != None or item != "":
            item = item.lower()
        if synonym != None or synonym != "":
            synonym = synonym.lower()
        if storage != None or storage != "":
            storage = storage.lower()
        if place != None or place != "":
            place = place.lower()
        return item, synonym, storage, place
        
        
        

##Intent handlers
    @intent_handler('insert.item.intent')
    def handle_insert_item(self):
        item = self.get_response('insert.item.name',num_retries=0)
        synonym = self.get_response('insert.item.synonym',num_retries=0)
        if synonym == None:
            synonym = " "
        storage = self.get_response('insert.item.storage',num_retries=0)
        place = self.get_response('insert.item.place',num_retries=0)
        self.insert_new_item(item, synonym, storage, place)

    @intent_handler('insert.item.complete.intent')
    def handle_insert_item_completely(self, message):
        item = message.data.get('item')
        synonym = message.data.get('synonym')
        storage = message.data.get('storage')
        place = message.data.get('place')
        LOG.info(f"Gehört:  {item}, {synonym}, {storage} und {place}.")
        self.insert_new_item(item, synonym, storage, place)

    @intent_handler('add.synonym.intent')
    def handle_synonym(self, message):
        syn = message.data.get('syn')
        column = "t_synonym"
        self.update_last_insert(column,syn)

    @intent_handler('add.loc_one.intent')
    def handle_loc1(self, message):
        loc_one = message.data.get('loc_one')
        column = "t_storage"
        self.update_last_insert(column,loc_one)

    @intent_handler('add.loc_two.intent')
    def handle_loc2(self, message):
        loc_two = message.data.get('loc_two')
        column = "t_place"
        self.update_last_insert(column,loc_two)

    @intent_handler('find.item.intent')
    def handle_find_item(self, message):
        '''Looks for an item in column t_name. If search isn't successful\
            you are asked for looking in column t_synonym'''
        item = message.data.get('item')
        res = self.check_item_names_exact(item)
        if len(res) == 0:
            self.speak_dialog('look.for.synonym',{'item': item})
            res = self.check_item_synonyms(item)
            if len(res) == 0:
                self.speak_dialog('nosynonym', {'item': item})
                self.speak_dialog('no.item.name')
            else:
                self.make_utterance_from_synonym(res, item)
        else:
            self.make_utterance(res, item)

def create_skill():
    return MySqliteDatabaseAssistant()

