import os
import requests
import json
import sqlite3
import logging
import discord

from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

logging.basicConfig(filename='log.txt', filemode='a', 
                      format='%(asctime)s %(msecs)d- %(process)d -%(levelname)s - %(message)s', 
                      datefmt='%d-%b-%y %H:%M:%S %p' ,
                      level=logging.DEBUG)

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
pluralkit = "https://api.pluralkit.me/v1/"

# command prefix for the bot
client = commands.Bot(command_prefix = '\pkp ')

# pk-pal login message
@client.event
async def on_ready():
  await client.change_presence(status=discord.Status.online, activity=discord.Game('Online & Ready!'))
  logging.info(f'{client.user} has connected to Discord!')
    
    
# for checking if message sender has pluralkit
def check_PK(msg):
  pk_request = requests.get(pluralkit + "a/" + str(msg.author.id))
  if pk_request.status_code == requests.codes.ok:
    system_info = json.loads(pk_request.text)
    system = requests.get(pluralkit + "s/" + system_info["id"])
    system_info = json.loads(system.text)
    logging.info(str(msg.author.id) + " has successfully connected to PK API.")
    return system_info
  else:
    logging.error("Error: " + str(pk_request.status_code) + ". Either PK API is down or they have no PluralKit")
    return 0

# for using the database
def sys_db(user, command, *args):
  conn = sqlite3.connect('sys.db')
  curs = conn.cursor()
  #if there is no table, make one
  curs.execute('CREATE TABLE IF NOT EXISTS pkpal (user text, member text, messages text)')
  logging.info("Table available")
  info = [user]
  
  # if both a member and a message are passed to this function, add to table
  if len(args) == 2:
    for x in args:
      info.append(x)
    try:
      curs.execute('INSERT INTO pkpal VALUES (?,?,?)', (info[0],info[1],info[2],))
    except sqlite3.Warning:
      logging.warning("Caught an SQLite3 warning")
    except sqlite3.IntegrityError:
      logging.error("caught an SQLite3 Integrity Error")
    except sqlite3.ProgrammingError:
      logging.error("Caught an SQLite3 Programming Error")
    except sqlite3.OperationalError:
      logging.error("Caught an SQLite3 Operational Error")
    except sqlite3.NotSupportedError:
      logging.error("Caught an SQLite3 Not Supported Error")
    except:
      logging.error('Caught an unspecified error')
    else:
      # save changes
      conn.commit()
      logging.info("Message saved successfully.")
      # close database
      conn.close()
      logging.info("Database closed.")
      return 1
  # if only a member is passed to this function
  elif len(args) == 1:
    # get messages of member
    if command == 'read_message':
      to_pass = (str(user), ''.join(args))
      try:
        curs.execute('SELECT messages FROM pkpal WHERE user =? AND member =?', to_pass)
      except sqlite3.Warning:
        logging.warning("Caught an SQLite3 warning")
      except sqlite3.IntegrityError:
        logging.error("caught an SQLite3 Integrity Error")
      except sqlite3.ProgrammingError:
        logging.error("Caught an SQLite3 Programming Error")
      except sqlite3.OperationalError:
        logging.error("Caught an SQLite3 Operational Error")
      except sqlite3.NotSupportedError:
        logging.error("Caught an SQLite3 Not Supported Error")
      except:
        logging.error('Caught an unspecified error')
      else:
        logging.info("Messages obtained successfully.")
        messages = curs.fetchall()
        # close database
        conn.close()
        logging.info("Database closed.")
        return messages

    # clear messages of member
    elif command == 'clear':
      to_pass = (str(user), ''.join(args))
      try:
        curs.execute('DELETE FROM pkpal WHERE user =? AND member =?', to_pass)
      except sqlite3.Warning:
        logging.warning("Caught an SQLite3 warning")
      except sqlite3.IntegrityError:
        logging.error("caught an SQLite3 Integrity Error")
      except sqlite3.ProgrammingError:
        logging.error("Caught an SQLite3 Programming Error")
      except sqlite3.OperationalError:
        logging.error("Caught an SQLite3 Operational Error")
      except sqlite3.NotSupportedError:
        logging.error("Caught an SQLite3 Not Supported Error")
      except:
        logging.error('Caught an unspecified error')
      else:
        # save changes
        conn.commit()
        logging.info("Messages cleared successfully.")
        # close database
        conn.close()
        logging.info("Database closed.")
        return 1
  # or else raise an error
  else:
    logging.critical("No arguments have been passed to sys_db function")
    return 0

# checking if a member is in a system
def check_member(system_info, member):
  # connect to PK members list
  members = requests.get(pluralkit + "s/" + system_info["id"] + "/members")
  members_info = json.loads(members.text)
  
  # if PK list is functional check the member's name exists
  if members.status_code == requests.codes.ok:
    logging.info("Connected to members list of " + system_info["id"] + " system.")
    obt_member = {}
    for item in members_info:
      if (item['name'] == str(member)) or (item['name'] == str(member).capitalize()):
        obt_member.update(item)
        logging.info("Obtained " + item['name'] + " information.")
    return obt_member
  else:
    logging.debug("Could not connect to member list of " + str(context.author.id) + ".")
    return 0

# catching command errors
@client.event
async def on_command_error(context, error):
    if isinstance(error, commands.CommandNotFound):
        await context.channel.send('Could not parse.')

# for returning id of system that sent message
@client.command(aliases=['systemid', 'id'])
async def sysid(context):
  system_info = check_PK(context)
  logging.debug(str(context.author.id) + " requested system ID.")
  await context.channel.send("Your system ID is '" + system_info["id"] + "'.")

# for returning current fronter
@client.command(aliases=['sysfronter', 'fronters'])
async def fronter(context):
  system_info = check_PK(context)
  fronter_info = requests.get(pluralkit + "s/" + system_info["id"] + "/fronters")
  fronter = json.loads(fronter_info.text)
  logging.debug(str(context.author.id) + " requested current fronter.\n")
  await context.channel.send("Current fronter is " + fronter['members'][0]['name'])

# for saving a message for a system member
@client.command(aliases=['leavemsg', 'leavemessage', 'leaveamsg', 'leaveamessage'])
async def leave_message(context, member: str, *args):
  system_info = check_PK(context)
  logging.debug(str(context.author.id) + " requested to leave a message for " + member + ".")
  #get member info
  obt_member = check_member(system_info, member)
  # check if member was obtained from member list
  if obt_member == 0:
    await context.channel.send("Your PluralKit members list is unavailable")
  elif obt_member:
    message = ' '.join(args)
    # if there was a message, save it
    if message != '':
      if sys_db(context.author.id, 'leave_message', obt_member['name'], message) == 1:
        await context.channel.send("Message for " + obt_member['name'] + " saved successfully.")
      else:
        await context.channel.send("Bot error. Message not saved.")
    else:
      await context.channel.send("No message given so none saved")
  else:
    logging.debug(str(member).capitalize() + " not found in member's list")
    await context.channel.send(str(member).capitalize() + " not found in member's list")   

# for reading messages left for a system member
@client.command(aliases=['readmsg', 'readmsgs', 'readmessage', 'readmessages'])
async def read_message(context, member: str):
  system_info = check_PK(context)
  logging.debug(str(context.author.id) + " requested saved messages of " + member + ".")
  obt_member = check_member(system_info, member)
  # check if member was obtained from member list
  if obt_member == 0:
    await context.channel.send("Your PluralKit members list is unavailable")
  # if member was retrieved, get the saved messages for them
  elif obt_member:
    messages = sys_db(context.author.id, 'read_message', obt_member['name'])
    if messages:
      for item in messages:
        await context.channel.send(''.join(item))
    elif messages == []:
      await context.channel.send("No messages left for " + obt_member['name'] + ".")
    else:
      await context.channel.send("Bot error. Messages not obtained.")
  else:
    logging.debug(str(member).capitalize() + " not found in member's list")
    await context.channel.send(str(member).capitalize() + " not found in member's list")

# for clearing all messages left for a system member
@client.command(aliases=['clearmessage','clearmessages', 'clearmsgs', 'clearmsg'])
async def clear(context, member: str):
  system_info = check_PK(context)
  logging.debug(str(context.author.id) + " requested to clear messages for " + member + ".")
  obt_member = check_member(system_info, member)
  # check if member was obtained from member list
  if obt_member == 0:
    await context.channel.send("Your PluralKit members list is unavailable")
  # if member was retrieved, clear their messages
  elif obt_member:
    if sys_db(context.author.id, 'clear', obt_member['name']) == 1:
      await context.channel.send("Messages of " + obt_member['name'] + " cleared.")
    else:
      await context.channel.send("Bot error. Messages not cleared.")
  else:
    logging.debug(str(member).capitalize() + " not found in member's list")
    await context.channel.send(str(member).capitalize() + " not found in member's list")

client.run(TOKEN)
