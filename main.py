import pyrogram
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import time
import os
import threading
import json

with open('config.json', 'r') as f: DATA = json.load(f)
def getenv(var): return os.environ.get(var) or DATA.get(var, None)

bot_token = getenv("TOKEN") 
api_hash = getenv("HASH") 
api_id = getenv("ID")
# YENİ: Forward edilecek kanal ID'si - config.json'a "FORWARD_CHANNEL" ekleyin veya environment variable olarak ayarlayın
forward_channel_id = getenv("FORWARD_CHANNEL")  # Örnek: -1001234567890 (kanal ID'si)

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


# YENİ FONKSİYON: Medyayı belirtilen kanala forward et
def forward_to_channel(file_path, msg_type, msg, original_message):
	"""Medyayı belirtilen kanala forward eder"""
	if forward_channel_id is None:
		return  # Forward kanal ID'si ayarlanmamışsa çık
	
	try:
		if msg_type == "Document":
			try:
				thumb = acc.download_media(msg.document.thumbs[0].file_id) if msg.document.thumbs else None
			except: 
				thumb = None
			
			bot.send_document(forward_channel_id, file_path, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities)
			if thumb: os.remove(thumb)

		elif msg_type == "Video":
			try: 
				thumb = acc.download_media(msg.video.thumbs[0].file_id) if msg.video.thumbs else None
			except: 
				thumb = None

			bot.send_video(forward_channel_id, file_path, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities)
			if thumb: os.remove(thumb)

		elif msg_type == "Animation":
			bot.send_animation(forward_channel_id, file_path)
			   
		elif msg_type == "Sticker":
			bot.send_sticker(forward_channel_id, file_path)

		elif msg_type == "Voice":
			bot.send_voice(forward_channel_id, file_path, caption=msg.caption, caption_entities=msg.caption_entities)

		elif msg_type == "Audio":
			try:
				thumb = acc.download_media(msg.audio.thumbs[0].file_id) if msg.audio.thumbs else None
			except: 
				thumb = None
				
			bot.send_audio(forward_channel_id, file_path, caption=msg.caption, caption_entities=msg.caption_entities)   
			if thumb: os.remove(thumb)

		elif msg_type == "Photo":
			bot.send_photo(forward_channel_id, file_path, caption=msg.caption, caption_entities=msg.caption_entities)

		elif msg_type == "Text":
			bot.send_message(forward_channel_id, msg.text, entities=msg.entities)

		print(f"✅ Medya başarıyla kanala forward edildi: {msg_type}")
		
	except Exception as e:
		print(f"❌ Kanala forward etme hatası: {e}")


# start command
@bot.on_message(filters.command(["start"]))
def send_start(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
	forward_status = f"\n\n**🔄 Auto Forward: {'Aktif' if forward_channel_id else 'Pasif'}**" if forward_channel_id else ""
	bot.send_message(message.chat.id, f"__Hg kardes**{message.from_user.mention}**, içerik kısıtlaması olan kanallardan içeriklere iş koyuyorum__{forward_status}\n\n{USAGE}",
	reply_markup=InlineKeyboardMarkup([[ InlineKeyboardButton("bir denujke yapımı", url="https://www.youtube.com/watch?v=MJK5VTEPD-w")]]), reply_to_message_id=message.id)


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

		datas = message.text.split("/")
		temp = datas[-1].replace("?single","").split("-")
		fromID = int(temp[0].strip())
		try: toID = int(temp[1].strip())
		except: toID = fromID

		for msgid in range(fromID, toID+1):

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

				try: msg  = bot.get_messages(username,msgid)
				except UsernameNotOccupied: 
					bot.send_message(message.chat.id,f"**The username is not occupied by anyone**", reply_to_message_id=message.id)
					return
				try:
					if '?single' not in message.text:
						bot.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
						# YENİ: Public mesajları da kanala forward et
						if forward_channel_id:
							try:
								bot.copy_message(forward_channel_id, msg.chat.id, msg.id)
								print("✅ Public mesaj kanala forward edildi")
							except Exception as e:
								print(f"❌ Public mesaj forward hatası: {e}")
					else:
						bot.copy_media_group(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
						# YENİ: Media group'u da kanala forward et
						if forward_channel_id:
							try:
								bot.copy_media_group(forward_channel_id, msg.chat.id, msg.id)
								print("✅ Media group kanala forward edildi")
							except Exception as e:
								print(f"❌ Media group forward hatası: {e}")
				except:
					if acc is None:
						bot.send_message(message.chat.id,f"**String Session is not Set**", reply_to_message_id=message.id)
						return
					try: handle_private(message,username,msgid)
					except Exception as e: bot.send_message(message.chat.id,f"**Error** : __{e}__", reply_to_message_id=message.id)

			# wait time
			time.sleep(3)


# handle private
def handle_private(message: pyrogram.types.messages_and_media.message.Message, chatid: int, msgid: int):
		msg: pyrogram.types.messages_and_media.message.Message = acc.get_messages(chatid,msgid)
		msg_type = get_message_type(msg)

		if "Text" == msg_type:
			bot.send_message(message.chat.id, msg.text, entities=msg.entities, reply_to_message_id=message.id)
			# YENİ: Text mesajını da kanala forward et
			if forward_channel_id:
				forward_to_channel(None, msg_type, msg, message)
			return

		smsg = bot.send_message(message.chat.id, '__Downloading__', reply_to_message_id=message.id)
		dosta = threading.Thread(target=lambda:downstatus(f'{message.id}downstatus.txt',smsg),daemon=True)
		dosta.start()
		file = acc.download_media(msg, progress=progress, progress_args=[message,"down"])
		os.remove(f'{message.id}downstatus.txt')

		upsta = threading.Thread(target=lambda:upstatus(f'{message.id}upstatus.txt',smsg),daemon=True)
		upsta.start()
		
		if "Document" == msg_type:
			try:
				thumb = acc.download_media(msg.document.thumbs[0].file_id)
			except: thumb = None
			
			bot.send_document(message.chat.id, file, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message,"up"])
			if thumb != None: os.remove(thumb)

		elif "Video" == msg_type:
			try: 
				thumb = acc.download_media(msg.video.thumbs[0].file_id)
			except: thumb = None

			bot.send_video(message.chat.id, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message,"up"])
			if thumb != None: os.remove(thumb)

		elif "Animation" == msg_type:
			bot.send_animation(message.chat.id, file, reply_to_message_id=message.id)
			   
		elif "Sticker" == msg_type:
			bot.send_sticker(message.chat.id, file, reply_to_message_id=message.id)

		elif "Voice" == msg_type:
			bot.send_voice(message.chat.id, file, caption=msg.caption, thumb=thumb, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message,"up"])

		elif "Audio" == msg_type:
			try:
				thumb = acc.download_media(msg.audio.thumbs[0].file_id)
			except: thumb = None
				
			bot.send_audio(message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message,"up"])   
			if thumb != None: os.remove(thumb)

		elif "Photo" == msg_type:
			bot.send_photo(message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id)

		# YENİ: İşlem tamamlandıktan sonra medyayı kanala forward et
		if forward_channel_id:
			forward_to_channel(file, msg_type, msg, message)

		os.remove(file)
		if os.path.exists(f'{message.id}upstatus.txt'): os.remove(f'{message.id}upstatus.txt')
		bot.delete_messages(message.chat.id,[smsg.id])


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


USAGE = """**herkese açık kanallara iş koyma**

__sadece gönderi linki gönder__

**özel kanallara iş koyma**

__öncelikle sohbetin davet bağlantısını gönder sonra gönderinin/gönderilerin bağlantısını gönder__

**botlara iş koyma**

__'/b/', botun kullanıcı adı ve mesaj kimliği ile bağlantı gönder__

```
https://t.me/b/botusername/4321
```

**toplu iş koyma(favorim**

__örneği veriyorum cakkal değilsen anlarsın__

```
https://t.me/xxxx/1001-1010

https://t.me/c/xxxx/101 - 120
```

__+18 içeriklere iş koymak yasaktır.__

**🔄 Auto Forward Özelliği Aktif!**
__Tüm forward edilen içerikler otomatik olarak belirlenen kanala da gönderilir.__
"""


# infinty polling
bot.run()

