import asyncio
from datetime import datetime, timezone
import logging
import os
import discord

logger = logging.getLogger(__name__)

def cleanValue(value):
    if value is None:
        return None
    value = str(value).strip()
    return None if value.casefold() in {"", "none", "null"} else value

def makeEmbed(event):
    uuid, old_value, old_rank, new_value, timestamp, kind, event_id, name = event
    old_value = cleanValue(old_value)
    new_value = cleanValue(new_value)
    player = discord.utils.escape_markdown(cleanValue(name) or uuid)
    if old_value == new_value:
        return None
    if kind == "name":
        if not old_value or not new_value:
            return None
        title = "Player Name Change"
        description = (
            "**Name Change**\n"
            f"{discord.utils.escape_markdown(old_value)} -> "
            f"{discord.utils.escape_markdown(new_value)}"
        )
        color = 0x3498DB
    elif old_value and new_value:
        title = "Guild Transfer"
        description = f"**Member Transfer**\n{player}"
        color = 0xF1C40F
    elif new_value:
        title = new_value
        description = f"**Member Join**\n{player}"
        color = 0x2ECC71
    elif old_value:
        title = old_value
        description = f"**Member Leave**\n{player}"
        color = 0xE74C3C
    else:
        return None

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.fromtimestamp(float(timestamp), tz=timezone.utc),
    )
    if kind == "membership":
        if old_value and new_value:
            embed.add_field(name="From", value=old_value)
            embed.add_field(name="To", value=new_value)
        rank = cleanValue(old_rank)
        if old_value and rank:
            embed.add_field(name="Previous Rank", value=rank.title())
    embed.set_footer(text=f"Detected by pyvalor | {uuid}")
    return embed

async def guildChangeFeed(valor):
    if os.getenv("TEST", "FALSE").upper() == "TRUE":
        return
    channel_id = int(os.getenv("GUILD_FEED_CHANNEL_ID", "1566842686835663060"))
    if not channel_id:
        return

    from sql import ValorSQL
    await valor.wait_until_ready()
    initialized = False
    while not valor.is_closed():
        try:
            channel = valor.get_channel(channel_id) or await valor.fetch_channel(channel_id)
            if not initialized:
                await ValorSQL.exec_param(
                    "INSERT IGNORE INTO dc_guildfeedS VALUES (%s, UNIX_TIMESTAMP())",
                    (channel_id,),
                )
                rows = await ValorSQL.exec_param(
                    "SELECT started_at FROM dc_guildfeedS WHERE channel_id = %s",
                    (channel_id,),
                )
                started_at = rows[0][0]
                columns = await ValorSQL._execute("SHOW COLUMNS FROM uuid_name_history")
                uuid_column, old_column, new_column, time_column = [
                    "`" + column[0].replace("`", "``") + "`" for column in columns
                ]
                initialized = True

            events = await ValorSQL.exec_param(f"""
SELECT pending.uuid, pending.old_value, pending.old_rank,
       pending.new_value, pending.event_time, pending.kind, pending.event_id,
       names.name
FROM (
    SELECT changes.*,
           SHA2(JSON_ARRAY(kind, uuid, old_value, old_rank, new_value, event_time), 256) AS event_id
    FROM (
        SELECT uuid, `old` AS old_value, old_rank, joined AS new_value,
               date AS event_time, 'membership' AS kind
        FROM guild_join_log
        WHERE date >= %s
        UNION
        SELECT {uuid_column}, {old_column}, NULL, {new_column}, {time_column}, 'name'
        FROM uuid_name_history
        WHERE {time_column} >= %s
    ) AS changes
) AS pending
LEFT JOIN dc_guildfeedD AS delivered
    ON delivered.channel_id = %s AND delivered.event_id = pending.event_id
LEFT JOIN uuid_name AS names ON names.uuid = pending.uuid
WHERE delivered.event_id IS NULL
ORDER BY pending.event_time, pending.event_id
LIMIT 100
""", (started_at, started_at, channel_id))
            for event in events:
                embed = makeEmbed(event)
                if embed is not None:
                    await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                await ValorSQL.exec_param(
                    "INSERT IGNORE INTO dc_guildfeedD VALUES (%s, %s)",
                    (channel_id, event[6]),
                )
        except Exception:
            logger.exception("Guild feed fail")
            await asyncio.sleep(60)
        else:
            await asyncio.sleep(5 if len(events) == 100 else 30)