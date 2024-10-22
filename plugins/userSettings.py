import logging
import asyncio 
from database import db
from config import Config
from translation import Translation
from pyrogram import Client, filters
from .test import get_configs, update_configs, CLIENT, parse_buttons
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CLIENT = CLIENT()



@Client.on_message(filters.private & filters.command(['userSettings']))
async def settings_user(client, message):
    text="<b>Change Your Settings As Your Wish</b>"
    await message.reply_text(
        text=text,
        reply_markup=main_buttons(),
        quote=True
    )
    


    
@Client.on_callback_query(filters.regex(r'^userSettings'))
async def user_settings_query(bot, query):
  logging.info(f"Callback data received: {query.data}")
  user_id = query.from_user.id
  i, type = query.data.split("#")
  buttons = [[InlineKeyboardButton('↩ Back', callback_data="userSettings#main")]]
  
  if type=="main":
     await query.message.edit_text(
       "<b>Cambia tu configuración como desees</b>",
       reply_markup=main_buttons())
           
  if type=="groups":
     buttons = []
     channels = await db.get_user_channels(user_id)                           #modificar user_chanels
     for channel in channels:
        buttons.append([InlineKeyboardButton(f"{channel['title']}",
                         callback_data=f"userSettings#editchannels_{channel['chat_id']}")])
     buttons.append([InlineKeyboardButton('✚ Add Grupo ✚', 
                      callback_data="userSettings#addchannel")])
     buttons.append([InlineKeyboardButton('↩ Back', 
                      callback_data="userSettings#main")])
     await query.message.edit_text( 
       "<b><u>Mis Grupos</u></b>\n\nPuede administrar sus chats objetivo aquí",
       reply_markup=InlineKeyboardMarkup(buttons))
   
  elif type=="addchannel":                                                    #modificar esat funcion
    await query.message.delete()
    logging.info("Iniciando el proceso para agregar un grupo.")
    
    try:
        text = await bot.send_message(user_id, "<b><u>Set Target Group</u></b>\n\nForward A Message From Your Target Group\n/cancel - To Cancel This Process")
        logging.info("Mensaje de instrucción enviado al usuario.")
        
        group_message = await bot.listen(chat_id=user_id, timeout=300)
        logging.info("Esperando un mensaje reenviado del usuario.")
        
        if group_message.text == "/cancel":
            await group_message.delete()
            logging.info("El usuario canceló el proceso.")
            return await text.edit_text(
                "Process Canceled",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        
        if not group_message.forward_date:
            await group_message.delete()
            logging.warning("El mensaje recibido no es un mensaje reenviado.")
            return await text.edit_text("This Is Not A Forward Message")
        
        # Verificación del tipo de chat
        if group_message.forward_from_chat is None:
            await group_message.delete()
            logging.warning("El mensaje reenviado no tiene un chat de origen.")
            return await text.edit_text("Please Forward A Message From A Group")
        
        if group_message.forward_from_chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            group_chat_id = group_message.forward_from_chat.id
            group_title = group_message.forward_from_chat.title
            group_username = group_message.forward_from_chat.username
            group_username = "@" + group_username if group_username else "private"
            
            logging.info(f"Grupo identificado: ID={group_chat_id}, Título={group_title}, Usuario={group_username}")
            group = await db.add_group(user_id, group_chat_id, group_title, group_username)
            await group_message.delete()
            
            logging.info("Grupo agregado a la base de datos.")
            await text.edit_text(
                "Successfully Updated" if group else "This Group Already Added",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await group_message.delete()
            logging.warning("El mensaje reenviado no proviene de un grupo.")
            return await text.edit_text("Please Forward A Message From A Group")
    
    except asyncio.exceptions.TimeoutError:
        logging.error("El proceso ha sido cancelado automáticamente debido a un timeout.")
        await text.edit_text('Process Has Been Automatically Cancelled', reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        logging.exception("Se produjo un error inesperado durante el proceso.")
        await text.edit_text("An error occurred. Please try again.")
             
  elif type=="adduserbot":
     await query.message.delete()
     user = await CLIENT.add_session(bot, query)
     if user != True: return
     await query.message.reply_text(
        "<b>Session Successfully Added To Database</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
      
  elif type=="bots": 
     bot = await db.get_bot(user_id)
     TEXT = Translation.BOT_DETAILS if bot['is_bot'] else Translation.USER_DETAILS
     buttons = [[InlineKeyboardButton('❌ Remove ❌', callback_data=f"userSettings#removebot")
               ],
               [InlineKeyboardButton('↩ Back', callback_data="userSettings#main")]]
     await query.message.edit_text(
        TEXT.format(bot['name'], bot['id'], bot['username']),
        reply_markup=InlineKeyboardMarkup(buttons))
                                             
  elif type=="removebot":
     await db.remove_bot(user_id)
     await query.message.edit_text(
        "Eliminado correctamente",
        reply_markup=InlineKeyboardMarkup(buttons))
                                             
  elif type.startswith("editchannels"): 
     chat_id = type.split('_')[1]
     chat = await db.get_channel_details(user_id, chat_id)
     buttons = [[InlineKeyboardButton('❌ Remove ❌', callback_data=f"userSettings#removechannel_{chat_id}")
               ],
               [InlineKeyboardButton('↩ Back', callback_data="userSettings#groups")]]
     await query.message.edit_text(
        f"<b><u>📄 Channel Details</b></u>\n\n<b>Title :</b> <code>{chat['title']}</code>\n<b>Channel ID :</b> <code>{chat['chat_id']}</code>\n<b>Username :</b> {chat['username']}",
        reply_markup=InlineKeyboardMarkup(buttons))
                                             
  elif type.startswith("removechannel"):
     chat_id = type.split('_')[1]
     await db.remove_channel(user_id, chat_id)
     await query.message.edit_text(
        "Eliminado correctamente",
        reply_markup=InlineKeyboardMarkup(buttons))
                               
  elif type=="caption":
     buttons = []
     data = await get_configs(user_id)
     caption = data['caption']
     if caption is None:
        buttons.append([InlineKeyboardButton('✚ Add Caption ✚', 
                      callback_data="userSettings#addcaption")])
     else:
        buttons.append([InlineKeyboardButton('👀 See Caption', 
                      callback_data="userSettings#seecaption")])
        buttons[-1].append(InlineKeyboardButton('🗑️ Delete Caption', 
                      callback_data="userSettings#deletecaption"))
     buttons.append([InlineKeyboardButton('↩ Back', 
                      callback_data="userSettings#main")])
     await query.message.edit_text(
        "<b><u>Custom Caption</b></u>\n\nYou Can Set A Custom Caption To Videos And Documents. Normaly Use Its Default Caption\n\n<b><u>Available Fillings :</b></u>\n\n<code>{filename}</code> : Filename\n<code>{size}</code> : File Size\n<code>{caption}</code> : Default Caption",
        reply_markup=InlineKeyboardMarkup(buttons))
                               
  elif type=="seecaption":   
     data = await get_configs(user_id)
     buttons = [[InlineKeyboardButton('✏️ Edit Caption', 
                  callback_data="userSettings#addcaption")
               ],[
               InlineKeyboardButton('↩ Back', 
                 callback_data="userSettings#caption")]]
     await query.message.edit_text(
        f"<b><u>Your Custom Caption</b></u>\n\n<code>{data['caption']}</code>",
        reply_markup=InlineKeyboardMarkup(buttons))
    
  elif type=="deletecaption":
     await update_configs(user_id, 'caption', None)
     await query.message.edit_text(
        "Successfully Updated",
        reply_markup=InlineKeyboardMarkup(buttons))
                              
  elif type=="addcaption":
     await query.message.delete()
     try:
         text = await bot.send_message(query.message.chat.id, "Send your custom caption\n/cancel - <code>cancel this process</code>")
         caption = await bot.listen(chat_id=user_id, timeout=300)
         if caption.text=="/cancel":
            await caption.delete()
            return await text.edit_text(
                  "Process Canceled !",
                  reply_markup=InlineKeyboardMarkup(buttons))
         try:
            caption.text.format(filename='', size='', caption='')
         except KeyError as e:
            await caption.delete()
            return await text.edit_text(
               f"Wrong Filling {e} Used In Your Caption. Change It",
               reply_markup=InlineKeyboardMarkup(buttons))
         await update_configs(user_id, 'caption', caption.text)
         await caption.delete()
         await text.edit_text(
            "Successfully Updated",
            reply_markup=InlineKeyboardMarkup(buttons))
     except asyncio.exceptions.TimeoutError:
         await text.edit_text('Process Has Been Automatically Cancelled', reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="button":
     buttons = []
     button = (await get_configs(user_id))['button']
     if button is None:
        buttons.append([InlineKeyboardButton('✚ Add Botón ✚', 
                      callback_data="userSettings#addbutton")])
     else:
        buttons.append([InlineKeyboardButton('👀 See Botón', 
                      callback_data="userSettings#seebutton")])
        buttons[-1].append(InlineKeyboardButton('🗑️ Desechar Botón ', 
                      callback_data="userSettings#deletebutton"))
     buttons.append([InlineKeyboardButton('↩ Back', 
                      callback_data="userSettings#main")])
     await query.message.edit_text(                                                                                  #modificar esto en deploy
        "<b><u>Botón personalizado</b></u>\n\nPuede configurar un botón en línea para mensajes.\n\n<b><u>Formato :</b></u>\n`[My bot][buttonurl:https://t.me/#]`\n",
        reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="addbutton":
     await query.message.delete()
     try:
         txt = await bot.send_message(user_id, text="**Envía tu botón personalizado.\n\nFORMATO:**\n`[My bot][buttonurl:https://t.me/#]`\n")
         ask = await bot.listen(chat_id=user_id, timeout=300)
         button = parse_buttons(ask.text.html)
         if not button:
            await ask.delete()
            return await txt.edit_text("Botón no válido")
         await update_configs(user_id, 'button', ask.text.html)
         await ask.delete()
         await txt.edit_text("Botón agregado con éxito",
            reply_markup=InlineKeyboardMarkup(buttons))
     except asyncio.exceptions.TimeoutError:
         await txt.edit_text('El proceso se ha cancelado automáticamente', reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="seebutton":
      button = (await get_configs(user_id))['button']
      button = parse_buttons(button, markup=False)
      button.append([InlineKeyboardButton("↩ Back", "userSettings#button")])
      await query.message.edit_text(
         "**Tu botón personalizado**",
         reply_markup=InlineKeyboardMarkup(button))
      
  elif type=="deletebutton":
     await update_configs(user_id, 'button', None)
     await query.message.edit_text(
        "Botón eliminado con éxito",
        reply_markup=InlineKeyboardMarkup(buttons))
   
 
  elif type.startswith("alert"):
    alert = type.split('_')[1]
    await query.answer(alert, show_alert=True)
      
def main_buttons():
  buttons = [[
       InlineKeyboardButton('🤖 Bᴏᴛs',
                    callback_data=f'userSettings#bots'),
       InlineKeyboardButton('👥 Grupos',
                    callback_data=f'userSettings#groups')
       ],[
       InlineKeyboardButton('🔘 Bᴏᴛóɴ',
                    callback_data=f'userSettings#button')
       ],
       [      
       InlineKeyboardButton('⌫ Bᴀᴄᴋ', callback_data='back')
       ]]
  return InlineKeyboardMarkup(buttons)
