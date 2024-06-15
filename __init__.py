from ovos_backend_client.api import DeviceApi
#from mycroft.api import DeviceApi
import lingua_franca
import sys
import os
import time
import sqlite3 as sq
from os.path import dirname, isfile
from adapt.intent import IntentBuilder
from mycroft.skills import intent_handler
from ovos_workshop.skills import OVOSSkill
from mycroft.util import play_audio_file
from ovos_bus_client.session import SessionManager
from ovos_utils import classproperty
from ovos_utils.process_utils import RuntimeRequirements
from ovos_utils.log import LOG
#test

class MySqliteDatabaseAssistant(OVOSSkill):
    def __init__(self):
        super(MySqliteDatabaseAssistant, self).__init__(name="My SQLite Database Assistant")

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
        self.con = sq.connect(self.db_adr, check_same_thread=False)
        self.cursor = self.con.cursor()


    def on_settings_changed(self):
        self.db_path = self.settings.get('db_path')
        self.db_file_01 = self.settings.get('db_filename_01')
        self.db_file_02 = self.settings.get('db_filename_02')
        self.db_adr = self.db_path + '/' + self.db_file_01
    
    def execute_sql(self, sql, tool=None, last_id=None):
        try:
            self.cursor.execute(sql)
            self.con.commit()
            if "INSERT" in sql:
                last_id = self.cursor.lastrowid
                self.write_lastid(last_id)
                self.speak_dialog('insert.succesfull', {'tool': tool})
            if "UPDATE" in sql:
                self.speak_dialog('update.succesfull',{'last_id': last_id})
        except sq.OperationalError as e:
            LOG.info(e)
            self.speak_dialog('no_database',{'database': self.db_file_01})
            return
    
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
    def check_tool_names_exact(self, tool):
        """Checks if a tool exists and returns the ID"""
        sql = """
        SELECT t_name, t_synonym, t_storage, t_place FROM tool WHERE t_name LIKE '"""+ '%' + tool.lower() + '%'+"""';
        """
        self.execute_sql(sql, tool)
        res = self.cursor.fetchall()
        return res
    
    def check_tool_names_raw(self, tool):
        """Checks if a tool exists and returns the ID"""
        sql = """
        SELECT t_name, t_synonym, t_storage, t_place FROM tool WHERE t_name LIKE '"""+ '%' + tool.lower() + '%'+"""';
        """
        self.execute_sql(sql)
        res = self.cursor.fetchall()
        return res
    

    def check_tool_synonyms(self, tool):
        """Checks if a tool exists and returns the ID"""
        sql = """
        SELECT t_name, t_synonym, t_storage, t_place FROM tool WHERE t_synonym LIKE '"""+ '%' + tool.lower() + '%'+"""';
        """
        self.execute_sql(sql)
        res = self.cursor.fetchall()
        return res
    
    def insert_new_tool(self, tool, synonym, storage, place):
        stored_tool = self.check_tool_names_exact(tool)
        tool, synonym, storage, place = self.make_lower(tool, synonym, storage, place)
        sql = """
            INSERT INTO tool (key, t_name, t_synonym, t_storage, t_place) VALUES \
                (NULL, '""" + tool +"""', '""" + synonym + """', '""" + storage +"""',\
                 '""" + place +"""');
            """
        self.execute_sql(sql, tool=tool)
        #else:
            #self.speak_dialog('tool.is.stored', {'tool': tool})

    def insert_single_tool(self, tool):
        stored_tool = self.check_tool_names_exact(tool)
        sql = """
            INSERT INTO tool (key, t_name) VALUES \
                (NULL, '""" + tool.lower() +"""');
            """
        self.execute_sql(sql, tool)

    def update_last_insert(self, column, value):
        last_id = self.read_lastid()
        sql = """
            UPDATE tool set '""" + column + """' = '""" + value + """' where key = '""" + last_id + """';
            """
        self.execute_sql(sql, last_id=last_id)

## Helper functions
#Formatting data tuples to speech
    def make_utterance(self, res, tool):
        if len(res) == 0:
            self.speak_dialog('notool', {'tool': tool})
        else:
            i = 0
            while i < len(res):
                tool = res[i][0]
                storage = res[i][2]
                place = res[i][3]
                self.speak_dialog('tool.is.in', {'tool': tool, 'storage': storage, 'place': place})
                i += 1

    def make_utterance_from_synonym(self, res, tool):
        if len(res) == 0:
            self.speak_dialog('notool', {'tool': tool})
        else:
            i = 0
            while i < len(res):
                tool = res[i][0]
                synonym = res[i][1]
                storage = res[i][2]
                place = res[i][3]
                self.speak_dialog('synonym.is.in', {'tool': tool, 'synonym': synonym, 'storage': storage, 'place': place})
                time.sleep(1)
                i += 1

    def make_lower(self, tool, synonym, storage, place):
        if tool != None or tool != "":
            tool = tool.lower()
        if synonym != None or synonym != "":
            synonym = synonym.lower()
        if storage != None or storage != "":
            storage = storage.lower()
        if place != None or place != "":
            place = place.lower()
        return tool, synonym, storage, place
        
        
        

##Intent handlers
    @intent_handler('test.dialog.intent')
    def handle_test(self):
        response = self.get_response('test.response')
        self.speak("Die Antwort lautet ja.")
        self.speak_dialog('response', {'response': response})

#Deactivated cause it wont work with hivemind
    @intent_handler('insert.tool.intent')
    def handle_insert_tool(self):
        tool = self.get_response('insert.tool.name',num_retries=0)
        #time.sleep(2)
        synonym = self.get_response('insert.tool.synonym',num_retries=0)
        if synonym == None:
            synonym = " "
        #time.sleep(2)
        storage = self.get_response('insert.tool.storage',num_retries=0)
        #time.sleep(2)
        place = self.get_response('insert.tool.place',num_retries=0)
        self.insert_new_tool(tool, synonym, storage, place)

#    @intent_handler('insert.single.tool.intent')
#    def handle_insert_single_tool(self, message):
#        tool = message.data.get('tool')
#        self.insert_single_tool(tool)

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

    @intent_handler('find.tool.intent')
    def handle_find_tool(self, message):
        '''Looks for a tool in column t_name. If search isn't successful\
            you are asked for looking in column t_synonym'''
        tool = message.data.get('tool')
        res = self.check_tool_names_exact(tool)
        if len(res) == 0:
            answer = self.ask_yesno('look.for.synonym', {'tool': tool})
            if answer == 'yes':
                res = self.check_tool_synonyms(tool)
                if len(res) == 0:
                    self.speak_dialog('nosynonym', {'tool': tool})
                else:
                    self.make_utterance_from_synonym(res, tool)
            else:
                self.speak_dialog('no.tool.name')
                return
        else:
            self.make_utterance(res, tool)

def create_skill():
    return MySqliteDatabaseAssistant()

