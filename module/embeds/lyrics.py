#  ------------------------------------------------------------
#  Copyright (c) 2024 Rystal-Team
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
#  ------------------------------------------------------------
#
from datetime import datetime

# TODO: fix ping + shorten embed to 5 lines ty

from deep_translator import GoogleTranslator

import asyncio
import nextcord
import re

from nextcord import SelectOption
from config.loader import lang, type_color
from database.guild_handler import get_guild_language
from module.embeds.generic import Embeds
from module.emoji import get_emoji
from module.lyrics import get_available_languages, fetch_lyrics
from module.nextcord_jukebox.music_player import MusicPlayer
from module.nextcord_jukebox.exceptions import EmptyQueue, NothingPlaying
from module.nextcord_jukebox.song import Song

class_namespace = "music_class_title"

running = {}


class LyricsEmbed:
    def __init__(
        self,
        interaction: nextcord.Interaction,
        player: MusicPlayer,
        song: Song,
        data: list,
        link: str,
        thumbnail: str = None,
    ):
        self.interaction = interaction
        self.player = player
        self.thumbnail = thumbnail
        self.song = song
        self.title = self.song.title
        self.source_url = link
        self.is_timeout = False
        self.follow_up = None
        self.data = data
        self.captions = []
        self.joined = None
        self.last_line = 0
        self.next_update = 0.0

        super().__init__()

        self.loop_task = asyncio.create_task(self.auto_update())

    async def auto_update(self):
        await asyncio.sleep(1)
        while not self.is_timeout:
            if not self.song == await self.player.now_playing() or self.is_timeout:
                await self.timeout_self()
                break
            await self.update()
            await asyncio.sleep(0.1)

    async def update(self):
        try:
            self.song = await self.player.now_playing()
        except (NothingPlaying, EmptyQueue):
            embed = Embeds.message(
                title=lang[await get_guild_language(self.interaction.guild.id)][
                    class_namespace
                ],
                message=lang[await get_guild_language(self.interaction.guild.id)][
                    "nothing_is_playing"
                ],
                message_type="warn",
            )
            if self.follow_up is not None:
                await self.interaction.followup.edit_message(
                    message_id=self.follow_up.id, embed=embed, view=None
                )
            else:
                await self.interaction.message.edit(embed=embed, view=None)
            return

        self.title = self.song.title
        self.thumbnail = self.song.thumbnail
        self.captions.clear()

        for i in range(-2, 3):
            f = self.data[self.last_line + i]
            line = re.sub("\n", " ", f["text"]).strip()
            if i == 0:
                self.captions.append(f'**{line}**')
            else:
                self.captions.append(f'-# {line}')

            """try:
                f = self.data[self.last_line + i]
                line = re.sub("\n", " ", f["text"]).strip()
                if i == 0:
                    self.captions.append(f'**{line}**')
                else:
                    self.captions.append(f'-# {line}')
                    if self.last_line != 0:
                        if i > 0:
                            self.captions.append(f'-# {line}')

                    if self.last_line != len(self.data):
                        if i < 0:
                            self.captions.append(f'-# {line}')
            except KeyError:
                pass"""

        time_elapsed = self.song.timer.elapsed

        if time_elapsed < self.data[self.last_line]["end"]:
            print(f'stayed, start: {self.data[self.last_line]["start"]} elapsed: {time_elapsed} end: {self.data[self.last_line]["end"]} datatime.datatime.time.now(): {datetime.now()}')
            pass
        else:
            print(f'passed, start: {self.data[self.last_line]["start"]} elapsed: {time_elapsed} end: {self.data[self.last_line]["end"]} datatime.datatime.time.now(): {datetime.now()}')
            self.next_update = self.data[self.last_line + 1]
            self.last_line += 1

        self.joined = '\n'.join(self.captions)

        embed = nextcord.Embed(
            title=self.title,
            description=self.joined,
            color=type_color["list"],
            url=self.source_url,
        )

        if self.thumbnail is not None:
            embed.set_thumbnail(url=self.thumbnail)

        if self.follow_up is None:
            follow_up_id: nextcord.Message = await self.interaction.message.edit(
                embed=embed, view=None
            )
            self.follow_up = follow_up_id
        else:
            await self.interaction.followup.edit_message(
                message_id=self.follow_up.id, embed=embed
            )

    async def timeout_self(self):
        """Timeout the view and stop the auto-update task."""
        self.is_timeout = True
        await self.interaction.followup.edit_message(
            message_id=self.follow_up.id, view=None
        )


class TranslateDropdown(nextcord.ui.Select):
    def __init__(self, viewer,  guild_language, player, song, link):
        super().__init__(
            placeholder=lang[guild_language]["lyrics_translate_dropdown_placeholder"],
            min_values=1,
            max_values=1,
            options=[],

        )
        self.viewer = viewer
        self.link = link

        self.player = player
        self.song = song

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer()

        for _ in running:
            await running[interaction.guild.id][0].timeout_self()

        if not self.values[0][-1] == "*":
            captions = await fetch_lyrics(link=self.link, language_code=self.values[0])
        else:
            self.values[0] = self.values[0][:-1]
            captions = await fetch_lyrics(link=self.link, language_code=self.values[0], translate=True)

        menu = LyricsEmbed(
            interaction,
            player=self.player,
            song=self.song,
            data=captions,
            link=self.link,
        )

        await menu.update()
        running.setdefault(interaction.guild.id, []).append(menu)


class LyricsLangEmbed(nextcord.ui.View):
    def __init__(
        self,
        interaction: nextcord.Interaction,
        player: MusicPlayer,
        song: Song,
        link: str
    ):
        super().__init__(timeout=None)
        self.guild_lang = asyncio.run(get_guild_language(interaction.guild.id))
        self.data = GoogleTranslator().get_supported_languages(as_dict=True)
        self.available_sub = None
        self.index = 0
        self.message = None
        self.interaction = interaction
        self.items_per_page = 10
        self.total_pages = (len(self.data) - 1) // self.items_per_page + 1
        self.author_id = interaction.user.id
        self.bot = interaction.client
        self.options = None
        self.link = link
        self.player = player
        self.song = song

        self.dropdown = TranslateDropdown(self, self.guild_lang, self.player, self.song, self.link)
        self.add_item(self.dropdown)

    async def send_initial_message(self):
        self.available_sub = await get_available_languages(link=self.link)
        if self.available_sub:
            embed = await self.create_embed(True)
            self.update_buttons()
            self.update_dropdown()
            self.message = await self.interaction.followup.send(embed=embed, view=self)
        else:
            embed = await self.create_embed(False)
            self.message = await self.interaction.followup.send(embed=embed)

    async def create_embed(self, is_ok):
        if is_ok:
            joined = []
            options = []

            for i in self.available_sub:
                if i:
                    joined.append(
                        lang[self.guild_lang]['lyrics_language_name_provided'].format(
                            language=i,
                            language_code=self.available_sub[i],
                        )
                    )
                    options.append(
                        SelectOption(
                            label=i.capitalize(),
                            value=self.available_sub[i],
                        )
                    )
            for i in self.data:
                joined.append(
                    lang[self.guild_lang]['lyrics_language_name_translated'].format(
                        language=i,
                        language_code=self.data[i]
                    )
                )
                options.append(
                    SelectOption(
                        label=i.capitalize(),
                        description=lang[self.guild_lang]['lyrics_dropdown_option_translated'],
                        value=f'{self.data[i]}*',
                    )
                )

            start = self.index * self.items_per_page
            end = start + self.items_per_page
            sliced = joined[start:end]
            options = options[start:end]

            self.options = options
            data = '\n'.join(sliced)

            embed = nextcord.Embed(
                title=lang[self.guild_lang]['lyrics_title'],
                description=lang[self.guild_lang]["music_lang_list_footer"].format(
                    page=self.index + 1, total_pages=self.total_pages, data=data
                ),
                color=type_color["list"],
            )

            return embed
        else:
            embed = nextcord.Embed(
                title=lang[self.guild_lang]['lyrics_title'],
                description=lang[self.guild_lang]["lyrics_no_subtitles"],
                color=type_color["error"]
            )

            return embed

    @nextcord.ui.button(
        emoji=get_emoji("arrow_left"), style=nextcord.ButtonStyle.secondary
    )
    async def previous(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer()
        if interaction.user.id == self.author_id:
            if self.index > 0:
                self.index -= 1
                await self.update_message()
            else:
                await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title=lang[self.guild_lang]["music_lang_title"],
                        description=lang[self.guild_lang]["interaction_author_only"],
                        color=type_color["warn"],
                    ),
                    ephemeral=True,
                )

    @nextcord.ui.button(
        emoji=get_emoji("arrow_right"), style=nextcord.ButtonStyle.secondary
    )
    async def next(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer()
        if interaction.user.id == self.author_id:
            if self.index < self.total_pages - 1:
                self.index += 1
                await self.update_message()
        else:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title=lang[self.guild_lang]["music_lang_title"],
                    description=lang[self.guild_lang]["interaction_author_only"],
                    color=type_color["warn"],
                ),
                ephemeral=True,
            )

    async def update_message(self):
        embed = await self.create_embed(True)
        self.update_buttons()
        self.update_dropdown()
        await self.message.edit(embed=embed, view=self)

    def update_buttons(self):
        self.children[0].disabled = self.index == 0
        self.children[1].disabled = self.index == self.total_pages - 1

    def update_dropdown(self):
        self.dropdown.options = self.options

    async def on_timeout(self):
        await self.message.edit(view=None)