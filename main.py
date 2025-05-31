import pyrogram
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied, PeerIdInvalid, ChannelPrivate
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import time
import os
import threading
import json
import re

# config.json dosyasini yukle
# Nerede bu dosyalar? Tabii ki burada, botun beyninde!
with open('config.json', 'r') as f: DATA = json.load(f)
def getenv(var): return os.environ.get(var) or DATA.get(var, None)

BOT_TOKEN = getenv("TOKEN")
API_HASH = getenv("HASH")
API_ID = getenv("ID")

# Bot mucizesini baslat! Haydi bastan, haydi hayata!
bot = Client("mybot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Eger bir "string session" varsa, kullanici hesabi da devreye girsin.
# Yoksa, bot biraz yalniz kalabilir, ama sorun degil, hallederiz.
SESSION_STRING = getenv("STRING")
if SESSION_STRING is not None:
    acc = Client("myacc", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
    acc.start()
else:
    acc = None

# Kanal ID'si burada gizleniyor... Sir gibi!
# Ama /addchannel komutuyla ortaya cikiyor!
CHANNEL_ID = None
CHANNEL_ID_FILE = "channel_id.txt" # Kanal ID'sini kaydetmek icin dosya

# --- Kanal ID Yonetimi (ID'yi hafizaya alalim ki unutmasin!) ---
def load_channel_id():
    global CHANNEL_ID
    if os.path.exists(CHANNEL_ID_FILE):
        with open(CHANNEL_ID_FILE, "r") as f:
            try:
                CHANNEL_ID = int(f.read().strip())
                print(f"Kanal ID'si yuklendi: {CHANNEL_ID}. Botun favori kanali artik bu!")
            except ValueError:
                CHANNEL_ID = None
                print("Kaydedilen kanal ID'si bozuk. Sanki biri kablolari karistirmis!")
    else:
        # Eger dosya yoksa, config.json'dan yuklemeyi dene (ilk kurulus icin)
        config_channel_id = getenv("CHANNEL_ID")
        if config_channel_id:
            try:
                CHANNEL_ID = int(config_channel_id)
                print(f"Kanal ID'si config.json'dan yuklendi: {CHANNEL_ID}. Vee, dosyaya kaydedildi!")
                save_channel_id(CHANNEL_ID) # Kalici olmasi icin dosyaya kaydet
            except ValueError:
                CHANNEL_ID = None
                print("config.json'daki CHANNEL_ID gecersiz. Bot biraz sasirdi.")

def save_channel_id(new_channel_id):
    global CHANNEL_ID
    CHANNEL_ID = new_channel_id
    with open(CHANNEL_ID_FILE, "w") as f:
        f.write(str(new_channel_id))
    print(f"Kanal ID'si kaydedildi: {new_channel_id}. Artik unutmayacak!")

# Bot baslarken kanal ID'sini yukle
load_channel_id()

# --- Durum Fonksiyonlari (Indirme ve Yukleme Raporlari) ---
def downstatus(statusfile, message):
    while True:
        if os.path.exists(statusfile):
            break
    time.sleep(3) # Bir nefes al, sonra ise basla
    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()
        try:
            bot.edit_message_text(message.chat.id, message.id, f"__Indiriliyor__ : **{txt}**. Yuzde kac oldu? Bakiyoruz...")
            time.sleep(10) # 10 saniyede bir guncelle, cok hizli olmasin, basimiz doner.
        except Exception:
            time.sleep(5) # Bir aksilik oldu, biraz bekle ve tekrar dene

def upstatus(statusfile, message):
    while True:
        if os.path.exists(statusfile):
            break
    time.sleep(3) # Yine bir nefes alma molasi
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            bot.edit_message_text(message.chat.id, message.id, f"__Yukleniyor__ : **{txt}**. Bulutlara dogru!")
            time.sleep(10) # Yukleme de hizli olmasin, telif haklari var!
        except Exception:
            time.sleep(5) # Bir aksilik daha, sakin ol ve tekrar dene

def progress(current, total, message, media_type):
    # Yuzde kac tamamlandi? Hassas olalim, 0.1 yuzde bile onemli!
    with open(f'{message.id}{media_type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")

# --- Mesaj Tipi Yardimcisi (Bu ne bicim bir mesaj simdi?) ---
def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
    if msg.document: return "Document"
    if msg.video: return "Video"
    if msg.animation: return "Animation"
    if msg.sticker: return "Sticker"
    if msg.voice: return "Voice"
    if msg.audio: return "Audio"
    if msg.photo: return "Photo"
    if msg.text: return "Text"
    return None # Bilinmeyen bir tur. Botumuz bazen sasirabiliyor.

# --- Temel Medya Isleme Fonksiyonu (Her seyi o halleder!) ---
async def handle_msg_send(user_message: pyrogram.types.messages_and_media.message.Message, msg: pyrogram.types.messages_and_media.message.Message):
    msg_type = get_message_type(msg)

    if msg_type == "Text":
        await bot.send_message(user_message.chat.id, msg.text, entities=msg.entities, reply_to_message_id=user_message.id)
        if CHANNEL_ID:
            try:
                await bot.send_message(CHANNEL_ID, msg.text, entities=msg.entities)
                print(f"Yazi mesaj {msg.id} kanala ({CHANNEL_ID}) iletildi. Cok okuyan cok bilir!")
            except Exception as e:
                print(f"Yazi mesajini kanala iletirken hata: {e}. Bot biraz yazi-resim yeteneklerini gelistirmeli.")
        return

    smsg = await bot.send_message(user_message.chat.id, '__Indiriliyor__', reply_to_message_id=user_message.id)
    dosta = threading.Thread(target=lambda:downstatus(f'{user_message.id}downstatus.txt', smsg), daemon=True)
    dosta.start()
    file = await acc.download_media(msg, progress=progress, progress_args=[user_message,"down"])
    os.remove(f'{user_message.id}downstatus.txt')

    upsta = threading.Thread(target=lambda:upstatus(f'{user_message.id}upstatus.txt', smsg), daemon=True)
    upsta.start()

    thumb = None
    if hasattr(msg, 'thumbs') and msg.thumbs:
        try:
            thumb = await acc.download_media(msg.thumbs[0].file_id)
        except Exception:
            thumb = None # Kucuk resim yoksa, "Yok oyle bir resim!" deriz.

    send_args = {
        "chat_id": user_message.chat.id,
        "reply_to_message_id": user_message.id,
        "progress": progress,
        "progress_args": [user_message,"up"]
    }
    
    channel_send_args = {
        "chat_id": CHANNEL_ID
    }
    
    # Aciklamali medya icin ortak argumanlar
    if hasattr(msg, 'caption'):
        send_args["caption"] = msg.caption
        send_args["caption_entities"] = msg.caption_entities
        channel_send_args["caption"] = msg.caption
        channel_send_args["caption_entities"] = msg.caption_entities

    if msg_type == "Document":
        await bot.send_document(file, thumb=thumb, **send_args)
        if CHANNEL_ID:
            try:
                await bot.send_document(CHANNEL_ID, file, thumb=thumb, **channel_send_args)
                print(f"Belge ({file}) kanala ({CHANNEL_ID}) iletildi. Dosyalar yerini buldu!")
            except Exception as e:
                print(f"Belgeyi kanala iletirken hata: {e}. Botun kargocu yetenekleri gelismeli.")

    elif msg_type == "Video":
        send_args.update({
            "duration": msg.video.duration,
            "width": msg.video.width,
            "height": msg.video.height,
            "thumb": thumb
        })
        channel_send_args.update({
            "duration": msg.video.duration,
            "width": msg.video.width,
            "height": msg.video.height,
            "thumb": thumb
        })
        await bot.send_video(file, **send_args)
        if CHANNEL_ID:
            try:
                await bot.send_video(CHANNEL_ID, file, **channel_send_args)
                print(f"Video ({file}) kanala ({CHANNEL_ID}) iletildi. Simdi popkorn zamani!")
            except Exception as e:
                print(f"Videoyu kanala iletirken hata: {e}. Botumuzun sinema kariyeri riskte.")

    elif msg_type == "Animation":
        await bot.send_animation(user_message.chat.id, file, reply_to_message_id=user_message.id)
        if CHANNEL_ID:
            try:
                await bot.send_animation(CHANNEL_ID, file, caption=msg.caption, caption_entities=msg.caption_entities)
                print(f"Animasyon ({file}) kanala ({CHANNEL_ID}) iletildi. Hareketli seyler severiz!")
            except Exception as e:
                print(f"Animasyonu kanala iletirken hata: {e}. Botun cizgi film yetenegi zayif.")

    elif msg_type == "Sticker":
        await bot.send_sticker(user_message.chat.id, file, reply_to_message_id=user_message.id)
        if CHANNEL_ID:
            try:
                await bot.send_sticker(CHANNEL_ID, file)
                print(f"Sticker ({file}) kanala ({CHANNEL_ID}) iletildi. En sevdigim emojiler!")
            except Exception as e:
                print(f"Sticker'i kanala iletirken hata: {e}. Botumuz yeterince yapiskan degil herhalde.")

    elif msg_type == "Voice":
        send_args.update({"thumb": thumb}) # Sesli mesajlarin da kucuk resimleri olabilir
        channel_send_args.update({"thumb": thumb})
        await bot.send_voice(user_message.chat.id, file, **send_args)
        if CHANNEL_ID:
            try:
                await bot.send_voice(CHANNEL_ID, file, **channel_send_args)
                print(f"Sesli mesaj ({file}) kanala ({CHANNEL_ID}) iletildi. Bir ses bir nefes!")
            except Exception as e:
                print(f"Sesli mesaji kanala iletirken hata: {e}. Botun sesi mi kisildi acaba?")

    elif msg_type == "Audio":
        send_args.update({"thumb": thumb})
        channel_send_args.update({"thumb": thumb})
        await bot.send_audio(user_message.chat.id, file, **send_args)
        if CHANNEL_ID:
            try:
                await bot.send_audio(CHANNEL_ID, file, **channel_send_args)
                print(f"Audio ({file}) kanala ({CHANNEL_ID}) iletildi. Muzik ruhun gidasidir!")
            except Exception as e:
                print(f"Audio'yu kanala iletirken hata: {e}. Botumuzun kulaklari tikali galiba.")

    elif msg_type == "Photo":
        await bot.send_photo(user_message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=user_message.id)
        if CHANNEL_ID:
            try:
                await bot.send_photo(CHANNEL_ID, file, caption=msg.caption, caption_entities=msg.caption_entities)
                print(f"Fotograf ({file}) kanala ({CHANNEL_ID}) iletildi. Bir kare bin kelime!")
            except Exception as e:
                print(f"Fotografi kanala iletirken hata: {e}. Botun fotografcilik yetenekleri gelismeli.")

    if thumb and os.path.exists(thumb): # Kucuk resmi temizle, cop birakmayiz.
        os.remove(thumb)
    os.remove(file) # Dosyayi temizle, yer acalim!
    if os.path.exists(f'{user_message.id}upstatus.txt'): os.remove(f'{user_message.id}upstatus.txt')
    await bot.delete_messages(user_message.chat.id,[smsg.id]) # Durum mesajini da sil, daginiklik olmasin.

# --- Komutlar (Botumuzun emirleri) ---
@bot.on_message(filters.command(["start"]))
async def send_start(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    await bot.send_message(message.chat.id, f"__Sa **{message.from_user.mention}**, icerik kaydetme kisitlamasini kaldiriyorum!__\n\n{USAGE}",
    reply_markup=InlineKeyboardMarkup([[ InlineKeyboardButton("dev", url="https://t.me/denujke")]]), reply_to_message_id=message.id)

@bot.on_message(filters.command(["addchannel"]))
async def add_channel(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    if len(message.command) < 2:
        await message.reply_text(
            "Kanali eklemek icin lutfen kanal kullanici adini veya ID'sini (orn. `-100XXXXXXXXXX`) belirtin.\n\n"
            "**Ornekler:**\n"
            "`/addchannel @kanal_kullanici_adi`\n"
            "`/addchannel -1001234567890`\n"
            "Botumuz akilli ama biraz yardima ihtiyaci var!"
        )
        return

    target_channel = message.command[1]

    try:
        chat = await client.get_chat(target_channel)
        if chat.type != "channel":
            await message.reply_text("**Hata:** Lutfen bir kanal kullanici adi veya ID'si girin. Grup veya kisi degil, kanal!")
            return

        save_channel_id(chat.id)
        await message.reply_text(f"✅ **Kanal basariyla ayarlandi!** Videolar ve diger icerikler artik `{chat.title}` kanalina iletilecek.\n"
                                 "Lutfen botun bu kanalda **yonetici yetkisine** sahip oldugundan ve `Mesaj Gonder` ile `Medya Gonder` izinlerinin verildiginden emin olun. Yoksa bot icerik gonderemez, sonra demedi demeyin!")

    except PeerIdInvalid:
        await message.reply_text("**Hata:** Gecersiz kanal kullanici adi veya ID'si. Yanlis adres verdiniz botumuza.")
    except ChannelPrivate:
        await message.reply_text("**Hata:** Bu ozel bir kanal. Botun string session hesabi kanalda uye mi veya davet baglantisi var mi, kontrol edin. Botumuz ajan degil, her yere giremez!")
    except Exception as e:
        await message.reply_text(f"Kanal eklenirken bir hata olustu: `{e}`. Botumuz uzgun :(")

@bot.on_message(filters.text & ~filters.command(["addchannel"]))
async def save(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    print(message.text) # Gelen mesaj neymis, bir bakalim.

    # Sohbetlere katilma (Davet linki yakalandi!)
    if "https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text:
        if acc is None:
            await bot.send_message(message.chat.id, f"**String Session ayarlanmadi.** Bu gorev icin asistana ihtiyacim var!", reply_to_message_id=message.id)
            return
        try:
            await acc.join_chat(message.text)
            await bot.send_message(message.chat.id, "**Sohbete katildim!** Merhaba millet!", reply_to_message_id=message.id)
        except UserAlreadyParticipant:
            await bot.send_message(message.chat.id, "**Zaten bu sohbetteyim.** Beni unutmus olmalisin :)", reply_to_message_id=message.id)
        except InviteHashExpired:
            await bot.send_message(message.chat.id, "**Davet linki gecersiz.** Bu linkin tarihi gecmis!", reply_to_message_id=message.id)
        except Exception as e:
            await bot.send_message(message.chat.id, f"**Hata** : __{e}__. Sohbete katilirken zorlandim.", reply_to_message_id=message.id)

    # Linkten mesaj alma
    elif "https://t.me/" in message.text:
        comment_id = None
        single_flag = False

        if "?single" in message.text:
            single_flag = True # Tek mesaj mi? Tamamdir!

        comment_match = re.search(r'[?&]comment=(\d+)', message.text)
        if comment_match:
            comment_id = int(comment_match.group(1)) # Yorum yakalandi!

        clean_url = re.sub(r'\?.*$', '', message.text) # Parametreleri temizle, linki saf haline getir.
        datas = clean_url.split("/")

        # Mesaj ID'sini duzgunce isle
        msg_id_part = datas[-1]
        temp = msg_id_part.split("-")

        try:
            fromID = int(temp[0].strip())
            toID = int(temp[1].strip()) if len(temp) > 1 else fromID
        except (IndexError, ValueError) as e:
            await bot.send_message(message.chat.id, f"**Hata** : __Mesaj ID formati gecersiz. Linkin dogru oldugundan emin ol.__ Botun kafasi karisti.", reply_to_message_id=message.id)
            print(f"Mesaj ID'si ayristirilirken hata: {e}")
            return

        for msgid in range(fromID, toID + 1):
            if comment_id is not None:
                await handle_comment(message, datas, msgid, comment_id, single_flag) # Yorum varsa, yorumu isle!
                continue

            if acc is None: # Ozel/bot sohbetleri icin acc kontrolu
                if "https://t.me/c/" in message.text or "https://t.me/b/" in message.text:
                    await bot.send_message(message.chat.id, f"**String Session ayarlanmadi.** Kilitli kapilar acilmiyor!", reply_to_message_id=message.id)
                    return

            try:
                if "https://t.me/c/" in message.text: # Ozel kanal
                    chatid = int("-100" + datas[4])
                    msg = await acc.get_messages(chatid, msgid)
                    await handle_msg_send(message, msg) # Mesaji kullaniciya gonder
                elif "https://t.me/b/" in message.text: # Bot sohbetti
                    username = datas[4]
                    msg = await acc.get_messages(username, msgid)
                    await handle_msg_send(message, msg) # Mesaji kullaniciya gonder
                else: # Herkese acik kanal
                    username = datas[3]
                    try:
                        msg = await bot.get_messages(username, msgid)
                        if not single_flag and not hasattr(msg, 'media_group_id'):
                            await bot.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
                        else:
                            # Eger medya grubuysa, tum grubu kopyala
                            if hasattr(msg, 'media_group_id'):
                                # media_group_msgs = await bot.get_media_group(msg.chat.id, msg.id) # Gerek yok, copy_media_group zaten hepsini halleder
                                await bot.copy_media_group(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
                            else: # single_flag dogruysa tek medyayi da kopyala
                                await bot.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)

                        # Kanal ID ayarliysa kanala da ilet
                        if CHANNEL_ID and (msg.video or msg.document or msg.photo or msg.animation or msg.audio or msg.voice or msg.sticker):
                            try:
                                if not single_flag and not hasattr(msg, 'media_group_id'):
                                    await bot.copy_message(CHANNEL_ID, msg.chat.id, msg.id)
                                    print(f"Herkese acik icerik ({msg.id}) kanala ({CHANNEL_ID}) iletildi. Bir kopyasi da oraya gitti!")
                                else: # Medya gruplari icin tum grubu kopyala
                                    if hasattr(msg, 'media_group_id'):
                                        await bot.copy_media_group(CHANNEL_ID, msg.chat.id, msg.id)
                                        print(f"Herkese acik medya grubu ({msg.id}) kanala ({CHANNEL_ID}) iletildi. Toplu tasimacilik!")
                                    else: # single_flag dogruysa tek medyayi da kopyala
                                        await bot.copy_message(CHANNEL_ID, msg.chat.id, msg.id)
                                        print(f"Herkese acik tek icerik ({msg.id}) kanala ({CHANNEL_ID}) iletildi. Klonlandi!")
                            except Exception as e:
                                print(f"Herkese acik icerigi kanala iletirken hata: {e}. Botun kargocu yetenekleri gelismeli.")

                    except UsernameNotOccupied:
                        await bot.send_message(message.chat.id, f"**Kullanici adi kimseye ait degil.** Bu adresi kimse kullanmiyor!", reply_to_message_id=message.id)
                        return
                    except Exception as e: # Kopyalama basarisiz olursa handle_private'a geri don (orn. kisitli icerik)
                        if acc is None:
                            await bot.send_message(message.chat.id, f"**String Session ayarlanmadi.** Ozel icerigi alamiyorum!", reply_to_message_id=message.id)
                            return
                        await handle_private(message, username, msgid) # username, get_messages icin chat_id olarak da kullanilabilir
            except Exception as e:
                await bot.send_message(message.chat.id,f"**Link islenirken hata**: __{e}__. Link bozuk galiba.", reply_to_message_id=message.id)
                print(f"Link islenirken beklenmedik hata: {e}")

            time.sleep(3) # Bekleme suresi. Acele ise seytan karisir!

# Yorum linklerini isle
async def handle_comment(message: pyrogram.types.messages_and_media.message.Message, datas: list, post_id: int, comment_id: int, single_flag: bool):
    if acc is None:
        await bot.send_message(message.chat.id, f"**String Session ayarlanmadi.** Yorumlara erisemiyorum, anahtarim yok!", reply_to_message_id=message.id)
        return

    try:
        # Ana kanal postu icin chat_id'yi belirle
        if "https://t.me/c/" in message.text:  # Ozel kanal
            channel_id_main = int("-100" + datas[4])
        else:  # Herkese acik kanal
            channel_id_main = datas[3]

        # Tartisma grubunu bulmak icin orijinal kanal postunu al
        channel_post = await acc.get_messages(channel_id_main, post_id)

        # Baglantili tartisma grubu ID'sini al
        discussion_id = None
        if hasattr(channel_post, 'replies') and channel_post.replies:
            discussion_id = channel_post.replies.channel_id
        elif hasattr(channel_post, 'linked_chat') and channel_post.linked_chat:
            discussion_id = channel_post.linked_chat.id

        if discussion_id:
            # Tartisma grubundan yorum mesajini almaya calis
            if single_flag: # Eger single_flag, medya grubu almaya calis
                try:
                    media_group = await acc.get_media_group(discussion_id, comment_id)
                    for media_msg in media_group:
                        await handle_msg_send(message, media_msg)
                except Exception as e: # Eger medya grubu degilse tek mesaja geri don
                    print(f"Yorum icin medya grubu alinirken hata, tek mesaja geri donuluyor: {e}")
                    comment_msg = await acc.get_messages(discussion_id, comment_id)
                    await handle_msg_send(message, comment_msg)
            else:
                comment_msg = await acc.get_messages(discussion_id, comment_id)
                await handle_msg_send(message, comment_msg)
        else:
            await bot.send_message(message.chat.id, f"**Bu kanal postu icin tartisma grubu bulunamadi.** Yorumlar nerede, kayip oldular!", reply_to_message_id=message.id)
    except Exception as e:
        await bot.send_message(message.chat.id, f"**Yorum islenirken hata**: __{e}__. Yorumu bulmak zor oldu.", reply_to_message_id=message.id)

# Ozel mesajlari isle (handle_msg_send icin bir sarici)
async def handle_private(message: pyrogram.types.messages_and_media.message.Message, chatid: int, msgid: int):
    msg: pyrogram.types.messages_and_media.message.Message = await acc.get_messages(chatid, msgid)
    await handle_msg_send(message, msg) # Artik her sey tek bir fonksiyonda isleniyor. Super, degil mi?

# --- Kullanim Talimatlari (Botu nasil kullanacagini ogren!) ---
USAGE = """**HERKESE ACIK KANALLAR ICIN**

__Sadece post linkini/linklerini gonder__

**OZEL KANALLAR ICIN**

__Once sohbetin davet linkini gonder (eger string session hesabi zaten sohbetin uyesi ise gerek yok)
Sonra post linkini/linklerini gonder__

**BOT SOHBETLERI ICIN**

__'/b/', botun kullanici adini ve mesaj ID'sini iceren linki gonder__

**COKLU POSTLAR ICIN**

__herkese acik/ozel post linklerini "baslangic - bitis" formatiyla gondererek birden fazla mesaj gonderebilirsin, https://t.me/c/xxxx/101 - 120 gibi__
"""


# infinty polling
bot.run()
