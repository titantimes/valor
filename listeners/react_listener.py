from valor import Valor
import discord
from util import ErrorEmbed, LongTextEmbed, info, LongFieldEmbed
from discord.utils import get
import time
from sql import ValorSQL
from dotenv import load_dotenv
import json
import os
import random

load_dotenv()
TEST = os.getenv("TEST") == "TRUE"
COUNCIL = int(os.getenv("COUNCILID"))
CABVOTE = int(os.getenv("CABVOTEID"))

async def _register_react_listener(valor: Valor):
    with open("assets/strat.json") as f:
        strat_stages = json.load(f)
    @valor.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        # REQUIRES MEMBER INTENT TO BE ENABLED IN DISCORD SETTINGS
        msg_id = payload.message_id

        rxn_chn = valor.get_channel(payload.channel_id)
        
        if payload.user_id != int(os.environ["SELFID"]) and valor.reaction_msg_ids.get(msg_id, 0) > int(time.time()):
            rls = {r.id for r in payload.member.roles}
            emoji = str(payload.emoji)
            if len(emoji) == 1:
                emoji = ord(emoji)
            else:
                emoji = int(emoji.split(":")[-1][:-1])
            res = await ValorSQL.get_react_msg_reaction(msg_id,  emoji)
            if not len(res):
                return
            
            res = res[0]
            if res[-1] == 'app':
                guild = valor.get_guild(payload.guild_id)
                config = (await ValorSQL.get_server_config(payload.guild_id))[0]
                category_id = config[1]
                category = get(guild.categories, id=category_id)
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    payload.member: discord.PermissionOverwrite(read_messages=True),
                    # payload.member: discord.PermissionOverwrite(view_channel=True),
                    # payload.member: discord.PermissionOverwrite(send_messages=True),
                }

                chn = await guild.create_text_channel(f"app-{config[2]+1}", overwrites=overwrites, category=category)
                await ValorSQL.server_config_set_app_cnt(payload.guild_id, config[2]+1)
                await chn.send(f"Hey, <@{payload.user_id}>", embed = LongTextEmbed("Fill This Out!", config[3], color=0xFFAA))

            # 535609000193163274 guild role
            elif res[-1] == "brilliance" and (535609000193163274 in rls or TEST):
                guild = valor.get_guild(payload.guild_id)
                config = (await ValorSQL.get_server_config(payload.guild_id))[0]
                category_id = config[1]
                category = get(guild.categories, id=category_id)

                cabinet_vote_role = guild.get_role(CABVOTE)
                council_role = guild.get_role(COUNCIL)

                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    payload.member: discord.PermissionOverwrite(read_messages=True),
                    council_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                    cabinet_vote_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
                }

                chn = await guild.create_text_channel(f"bril-{config[2]+1}", overwrites=overwrites, category=category, topic=str(payload.user_id))
                await ValorSQL.server_config_set_app_cnt(payload.guild_id, config[2]+1)
                await chn.send(f"Hey, <@{payload.user_id}>", embed = LongTextEmbed("Fill This Out!", config[9], color=0xFFAA))
            
            elif res[-1] == "spirit" and (535609000193163274 in rls or TEST):
                guild = valor.get_guild(payload.guild_id)
                config = (await ValorSQL.get_server_config(payload.guild_id))[0]
                category_id = config[1]
                category = get(guild.categories, id=category_id)

                cabinet_vote_role = guild.get_role(CABVOTE)
                council_role = guild.get_role(COUNCIL)

                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    payload.member: discord.PermissionOverwrite(read_messages=True),
                    council_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                    cabinet_vote_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
                }

                chn = await guild.create_text_channel(f"spir-{config[2]+1}", overwrites=overwrites, category=category, topic=str(payload.user_id))
                await ValorSQL.server_config_set_app_cnt(payload.guild_id, config[2]+1)
                await chn.send(f"Hey, <@{payload.user_id}>", embed = LongTextEmbed("Fill This Out!", config[10], color=0xFFAA))
            
            elif res[-1] == "fury" and (535609000193163274 in rls or TEST):
                guild = valor.get_guild(payload.guild_id)
                config = (await ValorSQL.get_server_config(payload.guild_id))[0]
                category_id = config[1]
                category = get(guild.categories, id=category_id)

                cabinet_vote_role = guild.get_role(CABVOTE)
                council_role = guild.get_role(COUNCIL)

                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    payload.member: discord.PermissionOverwrite(read_messages=True),
                    council_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                    cabinet_vote_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
                }

                chn = await guild.create_text_channel(f"fury-{config[2]+1}", overwrites=overwrites, category=category, topic=str(payload.user_id))
                await ValorSQL.server_config_set_app_cnt(payload.guild_id, config[2]+1)
                await chn.send(f"Hey, <@{payload.user_id}>", embed = LongTextEmbed("Fill This Out!", config[11], color=0xFFAA))

            elif res[-1] == 'captain' and ((1152706040299786271 in rls or 892886015017103360 in rls) or TEST):
                guild = valor.get_guild(payload.guild_id)
                config = (await ValorSQL.get_server_config(payload.guild_id))[0]
                category_id = config[1]
                category = get(guild.categories, id=category_id)

                # # give the user a blind role so they don't cheat
                # role = guild.get_role(config[5])
                # await payload.member.add_roles(role)

                council_role = guild.get_role(COUNCIL)
                cabinet_vote_role = guild.get_role(CABVOTE)

                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    payload.member: discord.PermissionOverwrite(read_messages=True),
                    council_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                    cabinet_vote_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                    # payload.member: discord.PermissionOverwrite(view_channel=True),
                    # payload.member: discord.PermissionOverwrite(send_messages=True),
                }

                chn = await guild.create_text_channel(f"cpt-{config[2]+1}", overwrites=overwrites, category=category, topic=str(payload.user_id))
                await ValorSQL.server_config_set_app_cnt(payload.guild_id, config[2]+1)
                await chn.send(f"Hey, <@{payload.user_id}>", embed = LongTextEmbed("Fill This Out!", config[6], color=0xFFAA))
            elif res[-1] == 'strategist' and (892881748646559754 in rls or TEST):
                guild = valor.get_guild(payload.guild_id)
                config = (await ValorSQL.get_server_config(payload.guild_id))[0]
                category_id = config[1]
                category = get(guild.categories, id=category_id)

                # # give the user a blind role so they don't cheat
                # role = guild.get_role(config[5])
                # await payload.member.add_roles(role)

                council_role = guild.get_role(COUNCIL)
                cabinet_vote_role = guild.get_role(CABVOTE)

                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    payload.member: discord.PermissionOverwrite(read_messages=True),
                    council_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                    cabinet_vote_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
                    # payload.member: discord.PermissionOverwrite(view_channel=True),
                    # payload.member: discord.PermissionOverwrite(send_messages=True),
                }

                chn = await guild.create_text_channel(f"strat-{config[2]+1}", overwrites=overwrites, category=category, topic=f"{payload.user_id},1")
                await ValorSQL.server_config_set_app_cnt(payload.guild_id, config[2]+1)
                em = LongTextEmbed("Section 1", strat_stages["1"], color=0xFFAA)

                await chn.send(f"Hey, <@{payload.user_id}>", embed = em)

        cabinets = {"bril", "spir", "fury"}
        # reaction to the green checkmark or thumbs up
        if payload.user_id != int(os.environ["SELFID"]):
            if str(payload.emoji) == '✅':
                config = await ValorSQL.get_server_config(payload.guild_id)
                if not len(config):
                    return
                config = config[0]
                if rxn_chn.category_id == config[1]:
                    msg = await rxn_chn.fetch_message(payload.message_id)
                    app_msg_id = int(msg.embeds[0].footer.text.split(' - ')[1])
                    app_type = msg.channel.name.split('-')[0]
                    
                    if app_type == "strat":
                        vote_chn = valor.get_channel(config[4])
                        taker_id, stage = msg.channel.topic.split(',')
                        message_format = f"`Strat App ({stage}/3) #%d - %s` - <@%s>\n" 
                        app_msg = await rxn_chn.fetch_message(app_msg_id)
                        
                        await vote_chn.send(message_format % (int(rxn_chn.name.split('-')[1]), rxn_chn.name.split('-')[0], taker_id))
                        await vote_chn.send("%s" % (app_msg.content))
                        
                        if stage == "1":
                            await msg.edit(embed=LongTextEmbed(f"Submitted Strategist Stage ({stage}/3)", "Proceed to the next section.", color=0xFF00))
                            # send section #2
                            em = LongTextEmbed("Section 2", strat_stages["2"], color=0xFFAA)
                            await rxn_chn.send("Fill this out", embed=em)

                        elif stage == "2":
                            await msg.edit(embed=LongTextEmbed(f"Submitted Strategist Stage ({stage}/3)", "Proceed to the next section.", color=0xFF00))
                            # send section #3
                            rng = random.randrange(0, 9)
                            em = LongTextEmbed("Section 3", strat_stages["3"].format(rng), color=0xFFAA)
                            em.set_image(url=strat_stages["maps"][rng])
                            await rxn_chn.send("Fill this out", embed=em)
                            
                        elif stage == "3":
                            await msg.edit(embed=LongTextEmbed("Submitted Strategist Stage (3/3)", "You have finished the strategist test. It's under review now", color=0xFF00))
                            await msg.channel.set_permissions(payload.member, send_messages=False, read_messages=True)
                            await msg.add_reaction('👍')

                        await msg.channel.edit(topic=f"{taker_id},{int(stage)+1}")
                        return

                    # CHECK STRAT STAGE FOR THIS
                    await msg.channel.set_permissions(payload.member, send_messages=False, read_messages=True)
                    await msg.edit(embed=LongTextEmbed("Submitted Application!", "Your application is currently under review.\nWe'll get back to you soon.", color=0xFF00))

                    await msg.add_reaction('👍')

                    if app_type in cabinets:
                        vote_chn = valor.get_channel(config[12])
                    else:
                        vote_chn = valor.get_channel(config[4])
                    app_msg = await rxn_chn.fetch_message(app_msg_id)

                    # # remove the blinded role
                    # guild = valor.get_guild(payload.guild_id)
                    # role = guild.get_role(config[5])
                    # await payload.member.remove_roles(role)

                    message_format = "`Application #%d - %s` - <@%d>\n" 
                    await vote_chn.send(message_format % (int(rxn_chn.name.split('-')[1]), rxn_chn.name.split('-')[0], app_msg.author.id))
                    await vote_chn.send("%s" % (app_msg.content))

            elif str(payload.emoji) == '👍':
                config = await ValorSQL.get_server_config(payload.guild_id)
                if not len(config):
                    return
                config = config[0]

                if "ticket" in rxn_chn.name: return # so it doesn't delete regular react channels

                if rxn_chn.category_id == config[1] and payload.member.guild_permissions.administrator:
                    await rxn_chn.delete()

