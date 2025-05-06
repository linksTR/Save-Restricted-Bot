import pyrogram
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import time
import os
import threading
import json
import re

with open('config.json', 'r') as f: DATA = json.load(f)
def getenv(var): return os.environ.get(var) or DATA.get(var, None)

bot_token = getenv("TOKEN") 
api_hash = getenv("HASH") 
api_id = getenv("ID")
bot = Client("mybot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

ss = getenv("STRING")
if ss is not None:
	acc = Client("myacc" ,api_id=api_id, api_hash=api_hash, session_string=ss)
	acc.start()
else: acc = None

# download status
def downstatus(statusfile,message):
	while True:
		if os.path.exists(statusfile):
			break

	time.sleep(3)      
	while os.path.exists(statusfile):
		with open(statusfile,"r") as downread:
			txt = downread.read()
		try:
			bot.edit_message_text(message.chat.id, message.id, f"__Downloaded__ : **{txt}**")
			time.sleep(10)
		except:
			time.sleep(5)


# upload status
def upstatus(statusfile,message):
	while True:
		if os.path.exists(statusfile):
			break

	time.sleep(3)      
	while os.path.exists(statusfile):
		with open(statusfile,"r") as upread:
			txt = upread.read()
		try:
			bot.edit_message_text(message.chat.id, message.id, f"__Uploaded__ : **{txt}**")
			time.sleep(10)
		except:
			time.sleep(5)


# progress writter
def progress(current, total, message, type):
	with open(f'{message.id}{type}status.txt',"w") as fileup:
		fileup.write(f"{current * 100 / total:.1f}%")


# start command
@bot.on_message(filters.command(["start"]))
def send_start(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
	bot.send_message(message.chat.id, f"__👋 Hi **{message.from_user.mention}**, I am Save Restricted Bot, I can send you restricted content by it's post link__\n\n{USAGE}",
	reply_markup=InlineKeyboardMarkup([[ InlineKeyboardButton("🌐 Source Code", url="https://github.com/bipinkrish/Save-Restricted-Bot")]]), reply_to_message_id=message.id)


@bot.on_message(filters.text)
def save(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
	print(message.text)

	# joining chats
	if "https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text:

		if acc is None:
			bot.send_message(message.chat.id,f"**String Session is not Set**", reply_to_message_id=message.id)
			return

		try:
			try: acc.join_chat(message.text)
			except Exception as e: 
				bot.send_message(message.chat.id,f"**Error** : __{e}__", reply_to_message_id=message.id)
				return
			bot.send_message(message.chat.id,"**Chat Joined**", reply_to_message_id=message.id)
		except UserAlreadyParticipant:
			bot.send_message(message.chat.id,"**Chat alredy Joined**", reply_to_message_id=message.id)
		except InviteHashExpired:
			bot.send_message(message.chat.id,"**Invalid Link**", reply_to_message_id=message.id)

	# getting message
	elif "https://t.me/" in message.text:
		# Extract comment id if present in the link
		comment_id = None
		single_flag = False
		
		# Check for ?single&comment= or ?comment= parameters
		if "?single" in message.text:
			single_flag = True
		
		comment_match = re.search(r'[?&]comment=(\d+)', message.text)
		if comment_match:
			comment_id = int(comment_match.group(1))
			
		# Clean URL for further processing
		clean_url = re.sub(r'\?.*$', '', message.text)
		
		datas = clean_url.split("/")
		temp = datas[-1].split("-")
		fromID = int(temp[0].strip())
		try: toID = int(temp[1].strip())
		except: toID = fromID

		for msgid in range(fromID, toID+1):
			# If this is a comment request, handle it differently
			if comment_id is not None:
				# For comment links, we need to get the message from the discussion group
				handle_comment(message, datas, msgid, comment_id, single_flag)
				continue
				
			# private
			if "https://t.me/c/" in message.text:
				chatid = int("-100" + datas[4])
				
				if acc is None:
					bot.send_message(message.chat.id,f"**String Session is not Set**", reply_to_message_id=message.id)
					return
				
				handle_private(message,chatid,msgid)
				# try: handle_private(message,chatid,msgid)
				# except Exception as e: bot.send_message(message.chat.id,f"**Error** : __{e}__", reply_to_message_id=message.id)
			
			# bot
			elif "https://t.me/b/" in message.text:
				username = datas[4]
				
				if acc is None:
					bot.send_message(message.chat.id,f"**String Session is not Set**", reply_to_message_id=message.id)
					return
				try: handle_private(message,username,msgid)
				except Exception as e: bot.send_message(message.chat.id,f"**Error** : __{e}__", reply_to_message_id=message.id)

			# public
			else:
				username = datas[3]

				try: msg = bot.get_messages(username,msgid)
				except UsernameNotOccupied: 
					bot.send_message(message.chat.id,f"**The username is not occupied by anyone**", reply_to_message_id=message.id)
					return
				try:
					if not single_flag:
						bot.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
					else:
						bot.copy_media_group(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
				except:
					if acc is None:
						bot.send_message(message.chat.id,f"**String Session is not Set**", reply_to_message_id=message.id)
						return
					try: handle_private(message,username,msgid)
					except Exception as e: bot.send_message(message.chat.id,f"**Error** : __{e}__", reply_to_message_id=message.id)

			# wait time
			time.sleep(3)


# Handle comment links
def handle_comment(message: pyrogram.types.messages_and_media.message.Message, datas: list, post_id: int, comment_id: int, single_flag: bool):
	if acc is None:
		bot.send_message(message.chat.id, f"**String Session is not Set**", reply_to_message_id=message.id)
		return
	
	try:
		if "https://t.me/c/" in message.text:  # Private channel
			channel_id = int("-100" + datas[4])
			# Get the original channel post to find linked discussion group
			channel_post = acc.get_messages(channel_id, post_id)
		else:  # Public channel
			channel_username = datas[3]
			# Get the original channel post to find linked discussion group
			channel_post = acc.get_messages(channel_username, post_id)
		
		# Get the linked discussion group
		if hasattr(channel_post, 'replies') and channel_post.replies:
			discussion_id = channel_post.replies.channel_id
			
			# Try to get the comment message from the discussion group
			comment_msg = acc.get_messages(discussion_id, comment_id)
			
			# Handle based on message type
			msg_type = get_message_type(comment_msg)
			
			# For media groups with single flag
			if single_flag and hasattr(comment_msg, 'media_group_id'):
				# Get the whole media group
				media_group = acc.get_media_group(discussion_id, comment_id)
				for media_msg in media_group:
					handle_msg_send(message, media_msg)
			else:
				# Regular message
				handle_msg_send(message, comment_msg)
		else:
			bot.send_message(message.chat.id, f"**Could not find discussion group for this channel post**", reply_to_message_id=message.id)
	except Exception as e:
		bot.send_message(message.chat.id, f"**Error handling comment**: __{e}__", reply_to_message_id=message.id)


# Handle sending any message type
def handle_msg_send(user_message: pyrogram.types.messages_and_media.message.Message, msg: pyrogram.types.messages_and_media.message.Message):
	msg_type = get_message_type(msg)

	if "Text" == msg_type:
		bot.send_message(user_message.chat.id, msg.text, entities=msg.entities, reply_to_message_id=user_message.id)
		return

	smsg = bot.send_message(user_message.chat.id, '__Downloading__', reply_to_message_id=user_message.id)
	dosta = threading.Thread(target=lambda:downstatus(f'{user_message.id}downstatus.txt', smsg), daemon=True)
	dosta.start()
	file = acc.download_media(msg, progress=progress, progress_args=[user_message,"down"])
	os.remove(f'{user_message.id}downstatus.txt')

	upsta = threading.Thread(target=lambda:upstatus(f'{user_message.id}upstatus.txt', smsg), daemon=True)
	upsta.start()
	
	if "Document" == msg_type:
		try:
			thumb = acc.download_media(msg.document.thumbs[0].file_id)
		except: thumb = None
		
		bot.send_document(user_message.chat.id, file, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=user_message.id, progress=progress, progress_args=[user_message,"up"])
		if thumb != None: os.remove(thumb)

	elif "Video" == msg_type:
		try: 
			thumb = acc.download_media(msg.video.thumbs[0].file_id)
		except: thumb = None

		bot.send_video(user_message.chat.id, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=user_message.id, progress=progress, progress_args=[user_message,"up"])
		if thumb != None: os.remove(thumb)

	elif "Animation" == msg_type:
		bot.send_animation(user_message.chat.id, file, reply_to_message_id=user_message.id)
		   
	elif "Sticker" == msg_type:
		bot.send_sticker(user_message.chat.id, file, reply_to_message_id=user_message.id)

	elif "Voice" == msg_type:
		bot.send_voice(user_message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=user_message.id, progress=progress, progress_args=[user_message,"up"])

	elif "Audio" == msg_type:
		try:
			thumb = acc.download_media(msg.audio.thumbs[0].file_id)
		except: thumb = None
			
		bot.send_audio(user_message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=user_message.id, progress=progress, progress_args=[user_message,"up"])   
		if thumb != None: os.remove(thumb)

	elif "Photo" == msg_type:
		bot.send_photo(user_message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=user_message.id)

	os.remove(file)
	if os.path.exists(f'{user_message.id}upstatus.txt'): os.remove(f'{user_message.id}upstatus.txt')
	bot.delete_messages(user_message.chat.id,[smsg.id])


# handle private
def handle_private(message: pyrogram.types.messages_and_media.message.Message, chatid: int, msgid: int):
		msg: pyrogram.types.messages_and_media.message.Message = acc.get_messages(chatid,msgid)
		handle_msg_send(message, msg)


# get the type of message
def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
	try:
		msg.document.file_id
		return "Document"
	except: pass

	try:
		msg.video.file_id
		return "Video"
	except: pass

	try:
		msg.animation.file_id
		return "Animation"
	except: pass

	try:
		msg.sticker.file_id
		return "Sticker"
	except: pass

	try:
		msg.voice.file_id
		return "Voice"
	except: pass

	try:
		msg.audio.file_id
		return "Audio"
	except: pass

	try:
		msg.photo.file_id
		return "Photo"
	except: pass

	try:
		msg.text
		return "Text"
	except: pass


USAGE = """**FOR PUBLIC CHATS**

__just send post/s link__

**FOR PRIVATE CHATS**

__first send invite link of the chat (unnecessary if the account of string session already member of the chat)
then send post/s link__

**FOR BOT CHATS**

__send link with '/b/', bot's username and message id, you might want to install some unofficial client to get the id like below__

```
https://t.me/b/botusername/4321
```

**FOR COMMENTS**

__send link with '?comment=' parameter to get a specific comment from a channel post__

```
https://t.me/channelname/123?comment=456
https://t.me/channelname/123?single&comment=456
```

**MULTI POSTS**

__send public/private posts link as explained above with formate "from - to" to send multiple messages like below__

```
https://t.me/xxxx/1001-1010

https://t.me/c/xxxx/101 - 120
```

__note that space in between doesn't matter__
"""


# infinty polling
bot.run()
