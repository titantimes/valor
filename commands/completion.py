import discord
import os
import util
import discord.ext
from discord.ext.commands import Context
import requests
from valor import Valor


def getInfo(call):
    r = requests.get(call)
    return r.json()

class ErrorEmbed(discord.Embed):
    def __init__(self):
        super().__init__(title="Error", description="Should something be working? ping Andrew or Callum", color=discord.Color.red())



async def _register_completion(valor: Valor):
    desc = "Shows someone's completion across all characters"
    
    @valor.command()
    async def completion(ctx: Context, name):
        try:
            isUUID = False
            uuid = "84f90219-44c2-470b-8f42-d33a4efd2b08"
            enforce_limits = False

            # Max stats for goals
            max_stats = {"total": 1690, "combat": 106, "gathering": 132, "crafting": 132}

            url = f"https://api.wynncraft.com/v3/player/{uuid if isUUID else name}?fullResult"
            resp = getInfo(url)

            def color_percentage(color_value):

                green_value = "\033[1;32m"
                red_value = "\033[0;31m"
                yellow_value = "\033[1;33m"
                blue_value = "\033[1;36m"
                stop = "\033[0m"

                if color_value >= 0.96:
                    return f"{blue_value}{color_value:>7.3%}{stop} "

                if color_value <= 0:
                    return f"{red_value}{color_value:>7.3%}{stop} "
                
                if 0 < color_value < 0.3:
                    return f"{red_value}{color_value:>7.3%}{stop}"
                
                if 0.3 <= color_value < 0.8:
                    return f"{yellow_value}{color_value:>7.3%}{stop}"
                
                if 0.8 <= color_value < 0.96:
                    return f"{green_value}{color_value:>7.3%}{stop}"
                

                #return f"{red_value}{green_value} {color_value:>7.3%}"


            def show_total_progress(stats):
                purple = "\033[0;35m"
                sick_green = "\033[0;32m"
                other_blue = "\033[0;34m"
                reddy = "\033[1;31m"
                stop = "\033[0m"
                
                results = []
                total_count = 0
                total_max = 0
                results.append(
                    f"{other_blue}{'Total Level':>24}{stop}  | {stats['Level']:>7,} / {(max_total := max_stats['total'] * max_characters):>6,}  |"
                    f" {color_percentage(stats['Level'] / max_total)}")
                total_count += stats['Level']
                total_max += max_total
                
                results.append(f"{other_blue}{('Combat'):>24}{stop}  | {stats['Combat']:>7,} / {(max_combat := max_stats['combat'] * max_characters):>6,}  |"
                    f" {color_percentage(stats['Combat'] / max_combat)}")
                total_count += stats['Combat']
                total_max += max_combat
                
                # Profs
                for prof in ["Farming", "Fishing", "Mining", "Woodcutting"]:
                    results.append(f"{purple}{(prof):>24}{stop}  | {stats[prof]:>7,} /"
                        f" {(single_prof_level := max_stats['gathering'] * max_characters):>6,}  | {color_percentage(stats[prof] / single_prof_level)}")
                total_count += stats[prof]
                total_max += single_prof_level
                
                for prof in ["Alchemism", "Armouring", "Cooking", "Jeweling", "Scribing", "Tailoring", "Weaponsmithing", "Woodworking"]:
                    results.append(f"{purple}{prof:>24}{stop}  | {stats[prof]:>7,} /"
                        f" {(single_prof_level := max_stats['crafting'] * max_characters):>6,}  | {color_percentage(stats[prof] / single_prof_level)}")
                total_count += stats[prof]
                total_max += single_prof_level
                
                # Quests
                results.append(f"{sick_green}{'Main Quests':>24}{stop}  | {stats['Quests']:>7,} /"
                    f" {(total_quests := 137 * max_characters):>6,}  |"
                    f" {color_percentage(stats['Quests'] / total_quests)}")
                total_count += stats['Quests']
                total_max += total_quests
                results.append(f"{sick_green}{'Slaying Mini-Quests':>24}{stop}  |"
                    f" {stats['Slaying Mini-Quests']:>7,} / {(total_slaying := max_characters * 29):>6}  |"
                    f" {color_percentage(stats['Slaying Mini-Quests'] / total_slaying)}")
                total_count += stats['Slaying Mini-Quests']
                total_max += total_slaying
                results.append(f"{sick_green}{('Gathering Mini-Quests'):>24}{stop}  |"
                    f" {stats['Gathering Mini-Quests']:>7,} / {(total_gathering := 96 * max_characters):>6,}  |"
                    f" {color_percentage(stats['Gathering Mini-Quests'] / total_gathering)}")
                total_count += stats['Gathering Mini-Quests']
                total_max += total_gathering

                # # # Completionist
                results.append(f"{sick_green}{('Discoveries'):>24}{stop}  |"
                    f" {stats['Discoveries']:>7,} / {(total_discoveries := (105 + 496) * max_characters):>6,}  |"
                    f" {color_percentage(stats['Discoveries'] / total_discoveries)}")
                total_count += stats['Discoveries']
                total_max += total_discoveries
                
                # Dungeons
                results.append(f"{sick_green}{('Unique Dungeons'):>24}{stop}  |"
                    f" {stats['Unique Dungeon Completions']:>7,} / {(total_dungeons := max_characters * 18):>6,}  |"
                    f" {color_percentage(stats['Unique Dungeon Completions'] / total_dungeons)}")
                total_count += stats['Unique Dungeon Completions']
                total_max += total_dungeons
                
                # Raids
                results.append(f"{sick_green}{('Unique Raids'):>24}{stop}  |"
                    f" {stats['Unique Raid Completions']:>7,} / {(total_raids := 4 * max_characters):>6,}  |"
                    f" {color_percentage(stats['Unique Raid Completions'] / total_raids)}")
                total_count += stats['Unique Raid Completions']
                total_max += total_raids

                #Overall total
                overall_percentage = total_count / total_max
                results.append(f"{reddy}{'Overall Total':>24}{stop}  | {total_count:7,} / {total_max:>6,}  | {color_percentage(overall_percentage)}")
                return '\n'.join(results)


            characters = resp["characters"]
            rank = resp["supportRank"]
            max_characters = {None: 6, "vip": 9, "vipplus": 11, "hero": 14, "champion": 14}[rank]
            shamans = []
            account_total = {
                "Level": 0,
                "Combat": 0,
                "Farming": 0,
                "Fishing": 0,
                "Mining": 0,
                "Woodcutting": 0,
                "Alchemism": 0,
                "Armouring": 0,
                "Cooking": 0,
                "Jeweling": 0,
                "Scribing": 0,
                "Tailoring": 0,
                "Weaponsmithing": 0,
                "Woodworking": 0,
                "Quests": 0,
                "Slaying Mini-Quests": 0,
                "Gathering Mini-Quests": 0,
                "Discoveries": 0,
                "Unique Dungeon Completions": 0,
                "Dungeon Completions": 0,
                "Unique Raid Completions": 0,
                "Raid Completions": 0,
            }
            char_totals = {}

            for char_uuid, wynn_char in characters.items():

                # Class link
                cur_char = [char_uuid,
                            wynn_char["level"] + wynn_char["xp"] / 100]

                # Quest sorting
                content_quests = 0
                slaying_quests = 0
                prof_quests = 0
                for quest in wynn_char["quests"]:
                    if "Mini-Quest - Gather" in quest:
                        prof_quests += 1
                    elif "Mini-Quest" in quest:
                        slaying_quests += 1
                    else:
                        content_quests += 1

                dungeon_names = [
                    "Skeleton", "Spider", "Decrepit Sewers", "Lost Sanctuary", "Infested Pit", 
                    "Sand-Swept Tomb", "Ice Barrows", "Undergrowth Ruins", "Galleon's Graveyard", 
                    "Corrupted Decrepit Sewers", "Corrupted Ice Barrows", "Corrupted Lost Sanctuary", 
                    "Corrupted Infested Pit", "Corrupted Sand-Swept Tomb", "Eldritch Outlook", 
                    "Fallen Factory", "Corrupted Undergrowth Ruins", "Corrupted Galleon's Graveyard", 
                    "Underworld Crypt", "Timelost Sanctum", "Ice", "Jungle", "Silverfish", "Zombie"
                ]
                dungeons_completed = sum(1 for dungeon in wynn_char["dungeons"]["list"] if any(name in dungeon for name in dungeon_names))


                raids_completed = 0
                for raid in wynn_char["raids"]["list"]:
                    if "The Canyon Colossus" in raid:
                        raids_completed += 1
                    if "Orphion's Nexu of Light" in raid:
                        raids_completed += 1
                    if "The Nameless Anomaly" in raid:
                        raids_completed += 1
                    if "Nest of the Grootslangs" in raid:
                        raids_completed += 1
                    else:
                        raids_completed += 1

                # Class info
                char_totals[char_uuid] = {
                    "Level": wynn_char["totalLevel"] + 12,
                    "Combat": wynn_char["level"],
                    "Farming": wynn_char["professions"]["farming"]["level"],
                    "Fishing": wynn_char["professions"]["fishing"]["level"],
                    "Mining": wynn_char["professions"]["mining"]["level"],
                    "Woodcutting": wynn_char["professions"]["woodcutting"]["level"],
                    "Alchemism": wynn_char["professions"]["alchemism"]["level"],
                    "Armouring": wynn_char["professions"]["armouring"]["level"],
                    "Cooking": wynn_char["professions"]["cooking"]["level"],
                    "Jeweling": wynn_char["professions"]["jeweling"]["level"],
                    "Scribing": wynn_char["professions"]["scribing"]["level"],
                    "Tailoring": wynn_char["professions"]["tailoring"]["level"],
                    "Weaponsmithing": wynn_char["professions"]["weaponsmithing"]["level"],
                    "Woodworking": wynn_char["professions"]["woodworking"]["level"],
                    "Quests": content_quests,
                    "Slaying Mini-Quests": slaying_quests,
                    "Gathering Mini-Quests": prof_quests,
                    "Discoveries": wynn_char["discoveries"],
                    "Unique Dungeon Completions": len(wynn_char["dungeons"]["list"]),
                    "Dungeon Completions": dungeons_completed,
                    "Unique Raid Completions": len(wynn_char["raids"]["list"]),
                    "Raid Completions": raids_completed,
                }

                if enforce_limits:
                    char_totals[char_uuid]["Discoveries"] = min(char_totals[char_uuid]["Discoveries"], 655)
                
                    

                for key, value in account_total.items():
                    account_total[key] = value + char_totals[char_uuid][key]
                

            stop = "\033[0m"
            bold = "\033[1m"

            # Main data
            account_total_br = show_total_progress(account_total)

            # code block not embed
            # print(f"```ansi\n{name}'s Completionism\n{account_total_br}\n```")
            await ctx.send(f"```ansi\n{bold}{name}'s Completionism{stop}\n{account_total_br}\n```")
        
        except Exception as e:
            await ctx.send(embed=ErrorEmbed())
            print(f"Error:{e}")
