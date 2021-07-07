from valor import Valor
import discord
from util import ErrorEmbed, LongTextEmbed, info, LongFieldEmbed
from discord.utils import get
import time
from sql import ValorSQL
from dotenv import load_dotenv
import os
import random

load_dotenv()

async def _register_react_listener(valor: Valor):
    @valor.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        # REQUIRES MEMBER INTENT TO BE ENABLED IN DISCORD SETTINGS
        msg_id = payload.message_id
        rxn_chn = valor.get_channel(payload.channel_id)
        
        if payload.user_id != int(os.environ["SELFID"]) and valor.reaction_msg_ids.get(msg_id, 0) > int(time.time()):
            emoji = str(payload.emoji)
            if len(emoji) == 1:
                emoji = ord(emoji)
            else:
                emoji = int(emoji.split(":")[-1][:-1])
            res = ValorSQL.get_react_msg_reaction(msg_id,  emoji)
            if not len(res):
                return
            
            res = res[0]
            if res[-1] == 'app':
                guild = valor.get_guild(payload.guild_id)
                config = ValorSQL.get_server_config(payload.guild_id)[0]
                category_id = config[1]
                category = get(guild.categories, id=category_id)
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    payload.member: discord.PermissionOverwrite(read_messages=True),
                    # payload.member: discord.PermissionOverwrite(view_channel=True),
                    # payload.member: discord.PermissionOverwrite(send_messages=True),
                }

                chn = await guild.create_text_channel(f"app-{config[2]+1}", overwrites=overwrites, category=category)
                ValorSQL.server_config_set_app_cnt(payload.guild_id, config[2]+1)
                await chn.send(f"Hey, <@{payload.member.id}>", embed = LongTextEmbed("Fill This Out!", config[3], color=0xFFAA))
            
            elif res[-1] == 'captain':
                guild = valor.get_guild(payload.guild_id)
                config = ValorSQL.get_server_config(payload.guild_id)[0]
                category_id = config[1]
                category = get(guild.categories, id=category_id)

                # # give the user a blind role so they don't cheat
                # role = guild.get_role(config[5])
                # await payload.member.add_roles(role)

                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    payload.member: discord.PermissionOverwrite(read_messages=True),
                    # payload.member: discord.PermissionOverwrite(view_channel=True),
                    # payload.member: discord.PermissionOverwrite(send_messages=True),
                }

                chn = await guild.create_text_channel(f"cpt-{config[2]+1}", overwrites=overwrites, category=category)
                ValorSQL.server_config_set_app_cnt(payload.guild_id, config[2]+1)
                await chn.send(f"Hey, <@{payload.member.id}>", embed = LongTextEmbed("Fill This Out!", config[6], color=0xFFAA))
            elif res[-1] == 'strategist':
                guild = valor.get_guild(payload.guild_id)
                config = ValorSQL.get_server_config(payload.guild_id)[0]
                category_id = config[1]
                category = get(guild.categories, id=category_id)

                # # give the user a blind role so they don't cheat
                # role = guild.get_role(config[5])
                # await payload.member.add_roles(role)

                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    payload.member: discord.PermissionOverwrite(read_messages=True),
                    # payload.member: discord.PermissionOverwrite(view_channel=True),
                    # payload.member: discord.PermissionOverwrite(send_messages=True),
                }

                chn = await guild.create_text_channel(f"strat-{config[2]+1}", overwrites=overwrites, category=category)
                ValorSQL.server_config_set_app_cnt(payload.guild_id, config[2]+1)
                em = LongTextEmbed("Fill This Out!", config[7], color=0xFFAA)
                em.set_image(url=random.choice([
                    "https://cdn.discordapp.com/attachments/839378628546527262/862435564192006164/g5f0TYGCvlmuJUd2vA4Hq_jBNBg1LjBGJx3fdvcJ01m_KtPNJEvZNqTwUldyq8IiQCDmncrvGZ3ZP_-_NcrSCrZ83wtP5wvjjKFd.png",
                    "https://cdn.discordapp.com/attachments/839378628546527262/862435597380616212/tI5DfvuT-IpBR9L4G4psMsb2GFP5eu174Kq-4I6115W6Yee86qURXO-Mao6XaqS0vlyRnxGtcI8LsXKDEK8KU2gNFBQ0ZkyiEtBH.png",
                    "https://cdn.discordapp.com/attachments/839378628546527262/862435645376167986/8L0R12AENbjKd_ejmRTAZdm8iGj6wCFzdC5VTk5wyo4ZfDteiQFNtIyEbmVMSxfSvQr5tr7BNU-W8SZofL4kN1CYiVslv54g9s6f.png",
                    "https://cdn.discordapp.com/attachments/839378628546527262/862435676411002880/coYXEeVjfFzooURtcNFkfnvIPCATxLjM-cX_T_OhFspP4qZ9ge2JbQZ1NysiJ6ejPj-uFGwCGArwueHpxGiZe0K7EEF0SW44pqMc.png"
                ]))
                await chn.send(f"Hey, <@{payload.member.id}>", embed = em)
        
        # reaction to the green checkmark or thumbs up
        if payload.user_id != int(os.environ["SELFID"]):
            if str(payload.emoji) == '✅':
                config = ValorSQL.get_server_config(payload.guild_id)
                if not len(config):
                    return
                config = config[0]
                if rxn_chn.category_id == config[1]:
                    msg = await rxn_chn.fetch_message(payload.message_id)
                    app_msg_id = int(msg.embeds[0].footer.text.split(' - ')[1])

                    await msg.edit(embed=LongTextEmbed("Submitted Application!", "Your application is currently under review.\nWe'll get back to you soon.", color=0xFF00))
                    await msg.channel.set_permissions(payload.member, send_messages=False, read_messages=True)
                    await msg.add_reaction('👍')

                    vote_chn = valor.get_channel(config[4])
                    app_msg = await rxn_chn.fetch_message(app_msg_id)
                    message_format = "`Application #%d` - <@%d>\n" \
                                     "```%s```"

                    # # remove the blinded role
                    # guild = valor.get_guild(payload.guild_id)
                    # role = guild.get_role(config[5])
                    # await payload.member.remove_roles(role)

                    await vote_chn.send(message_format % (int(rxn_chn.name.split('-')[1]), app_msg.author.id, app_msg.content))

            elif str(payload.emoji) == '👍':
                config = ValorSQL.get_server_config(payload.guild_id)
                if not len(config):
                    return
                config = config[0]

                if rxn_chn.category_id == config[1] and payload.member.guild_permissions.administrator:
                    await rxn_chn.delete()

