import logging
import asyncio 
from database import db
from config import Config
from translation import Translation
from pyrogram import Client, filters
from .test import get_configs, update_configs, CLIENT, parse_buttons, get_bot_groups
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from .utils import STS

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
  logging.info(f"Callback data received2: {type}")
  buttons = [[InlineKeyboardButton('↩ Back', callback_data="userSettings#main")]]
  _bot = await db.get_bot(user_id)
  
  if type=="main":
     await query.message.edit_text(
       "<b>Cambia tu configuración como desees</b>",
       reply_markup=main_buttons())
           
  if type=="groups":
     buttons = []
     channels = await db.get_user_channels(user_id)
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
   




  elif type == "addchannel":
    await query.message.delete()
    channels = await db.get_user_channels(user_id)
    try:
        logging.info("Iniciando el proceso para listar grupos del usuario.")
        
        text = await bot.send_message(user_id, "<b>🔄 Loading your groups...</b>")
        
        # Obtener grupos del usuario
        groups = []
        try:
            groups = await get_bot_groups(CLIENT.client(_bot))
        except Exception as e:  
            logging.error(f"Error al iniciar el cliente: {str(e)}")       
        if not groups:
            logging.warning("No se encontraron grupos.")
            return await text.edit_text(
                "No groups found!",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        try:
         existing_chat_ids = {channel['chat_id'] for channel in channels}
        except Exception as e:
            logging.error("esta aqui")
        # Filtrar grupos para obtener solo aquellos que no están en channels
        grupos_filtrados = [group for group in groups if group['id'] not in existing_chat_ids]
        # Crear botones para cada grupo
        group_buttons = []
        for group in grupos_filtrados:
            group_buttons.append([
                InlineKeyboardButton(
                    f"{group['title']}",
                    callback_data=f"userSettings#selectgroup_{group['id']}"
                )
            ])
        # Agregar botón de cancelar
        group_buttons.append([InlineKeyboardButton('↩ Back', callback_data="userSettings#main")])
        logging.info("hasta aqui bien")
        await text.edit_text(
           "<b>Select a group to add:</b>\n\n"
           "Choose from your groups below:",
           reply_markup=InlineKeyboardMarkup(group_buttons)
        )
        
        #Esperar la selección del usuario
        #try:
         #  callback_query = await bot.listen(
          #     chat_id=user_id,
           #    filters=filters.regex(r'^(selectgroup_)'),
            #   timeout=300
           #)
           #logging.warning("entro y se ejecuto esta parte")
           # Procesar la selección del grupo
           #selected_group_id = int(callback_query.data.replace("selectgroup_", ""))
           #logging
        # selected_group = next(
          #     (g for g in groups if g["id"] == selected_group_id),
          #     None
          # )
       
          # if not selected_group:
           #    raise ValueError("Selected group not found")
       
           # Guardar en la base de datos
         #  group = await db.add_channel(
          #     user_id,
          #     selected_group_id,
          #     selected_group['title'],
          #     selected_group['username']
          # )
       
           # Eliminar el grupo de la lista de grupos
          # grupos_filtrados = [g for g in grupos_filtrados if g["id"] != selected_group_id]
       
           # Actualizar la vista para eliminar el grupo seleccionado
          # group_buttons = []
         #  for group in grupos_filtrados:
         #      group_buttons.append([
          #         InlineKeyboardButton(
          #             f"{group['title']}",
          #             callback_data=f"userSettings#selectgroup_{group['id']}"
          #         )
          #     ])
            
           # Agregar botón de cancelar
          # group_buttons.append([InlineKeyboardButton('↩ Back', callback_data="userSettings#main")])
       
          # await text.edit_text(
           #    "<b>Select a group to add:</b>\n\n"
           #    "Choose from your groups below:",
           #    reply_markup=InlineKeyboardMarkup(group_buttons)
          # )
            
           #if group:
           #    logging.info("Grupo agregado exitosamente a la base de datos.")
           #    await text.edit_text(
           #        "Successfully Updated",
           #        reply_markup=InlineKeyboardMarkup(buttons)
            #   )
           #else:
            #   logging.info("El grupo ya estaba agregado en la base de datos.")
             #  await text.edit_text(
              #     "This Group Already Added",
               #    reply_markup=InlineKeyboardMarkup(buttons)
               #)
                
        #except asyncio.exceptions.TimeoutError:
           #logging.warning("El proceso ha sido cancelado automáticamente por timeout.")
    except Exception as e:
        logging.error(f"Error al enviar mensaje inicial: {str(e)}")
        await bot.send_message(
            user_id,
            f"❌ An error occurred while loading groups: {str(e)}"
        )        



    
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



    
  elif type.startswith("selectgroup"):
     logging.warning("Brinco bien hasta aqui id")
     chat_id = type.split('_')[1]
     logging.warning(f"Brinco bien hasta aqui id{chat_id}")
     groups = await get_bot_groups(CLIENT.client(_bot))
     logging.warning("Bien hasta aqui")
     try:
         selected_group = next(
                   (g for g in groups if g["id"] == chat_id),
                   None
         )
     except Exception as e:
         logging.error(f"Tuvo fallo en: {e}")
     try:    
         await db.add_channel(
                   user_id,
                   chat_id,
                   selected_group['title'],
                   selected_group['username']
              )
     except Exception as e:
         logging.error(f"Tuvo fallo en: {e}")
     logging.warning("Adiciono")
      #Eliminar el grupo de la lista de grupos
     grupos_filtrados = [g for g in groups if g["id"] != chat_id]
       
      #Actualizar la vista para eliminar el grupo seleccionado
     group_buttons = []
     for group in grupos_filtrados:
           group_buttons.append([
              InlineKeyboardButton(
                  f"{group['title']}",
                  callback_data=f"userSettings#selectgroup_{group['id']}"
              )
           ])
            
           #Agregar botón de cancelar
     group_buttons.append([InlineKeyboardButton('↩ Back', callback_data="userSettings#main")])
       
     await text.edit_text(
               "<b>Select a group to add:</b>\n\n"
               "Choose from your groups below:",
               reply_markup=InlineKeyboardMarkup(group_buttons)
           )
            


    
  
  
  
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

async def get_user_groups(client: Client):
    groups = []
    async for dialog in client.get_dialogs():
        if dialog.chat.type in ["group", "supergroup"]:
            groups.append({
                "id": dialog.chat.id,
                "title": dialog.chat.title,
                "username": dialog.chat.username,
                "members_count": dialog.chat.members_count
            })
    return groups
      
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
