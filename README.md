# <img src="https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/tools.svg" card_color="#22A7F0" width="50" height="50" style="vertical-align:bottom"/> My Sqlite Database Assistant
Mycroft Skill for adding records to a database using sqlite

## About
The initial goal is to develop database dialogs that allow you to enter and edit records in an SQLite database. Later the extension to create and configure arbitrary databases is planned.
Adding later (realy under construction, not working yet) 

## Examples
* "Hey Mycroft, add tool in database tools"
* "Hey Mycroft, where is the (tool) Hammer"
* "Hey Mycroft, do I have somethimg like a scriber"

## Setup
Before using the first time you have to edit file settings.json. you find it under ```~/.config/mycroft/skills/ovos-skill-my-sqlite.joergz2```. Please add the absolute path to database folder and a name for database file:
```
{
    "__mycroft_skill_firstrun": false,
    "db_path": "/absolute/path/to/database_folder/",
    "db_filename_01": "tools.db",
    "db_filename_02": ""
}
```

## Credits
JoergZ2

## Category
**Information**
Productivity

## Tags
#Database management

