from io import BytesIO
from typing import Optional

import nextcord
from PIL import Image, ImageDraw, ImageFont
from nextcord import File
from nextcord.ext import commands

from config.config import lang, theme_color
from database import user_handler
from database.guild_handler import get_guild_language
from module.embed import Embeds

class_namespace = "level_class_title"


class RankSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            data = await user_handler.get_user_data(message.author.id)

            xp = data["xp"]
            lvl = data["level"]

            increased_xp = xp + 25
            new_level = round(increased_xp / 100)

            data["xp"] = increased_xp

            if new_level > lvl:
                data["level"] = new_level
                data["xp"] = 0

            new_xp = int(data["xp"])
            userlvl = int(data["level"])
            usertotalxp = int(
                ((((userlvl * userlvl) / 2) + (userlvl / 2)) * 100) + new_xp
            )

            data["totalxp"] = usertotalxp
            await user_handler.update_user_data(message.author.id, data)

            if new_level > lvl:
                await message.channel.send(
                    lang[await get_guild_language(message.guild.id)]["level_up"].format(
                        user=message.author.mention, level=data["level"]
                    )
                )

    @nextcord.slash_command(description=class_namespace)
    async def rank(
        self,
        interaction: nextcord.Interaction,
    ):
        return

    @rank.subcommand(
        name="card",
        description="🎖️ | Get your rank or other member's rank!",
    )
    async def card(
        self,
        interaction: nextcord.Interaction,
        member: Optional[nextcord.User] = nextcord.SlashOption(
            name="member",
            description="Choose a user to view their rank!",
            required=False,
        ),
    ):
        await interaction.response.defer()

        if member is None:
            user = interaction.user
        else:
            user = member

        data = await user_handler.get_user_data(user.id)

        xp = data["xp"]
        lvl = data["level"]

        next_level_xp = (lvl + 1) * 100
        xp_need = next_level_xp
        xp_have = data["xp"]

        percentage = int(((xp_have * 100) / xp_need))

        if percentage < 1:
            percentage = 0

        # Rank card
        background = Image.open("./rankCardBase.png").convert("RGBA")
        profile = Image.open(BytesIO(await user.display_avatar.read())).convert("RGBA")
        profile = profile.resize((135, 135), Image.LANCZOS)
        mask = Image.new("L", profile.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + profile.size, fill=255)
        profile.putalpha(mask)

        background.paste(profile, (40, 70), profile)

        draw = ImageDraw.Draw(background)
        font_paths = {
            "title": "./font/GoNotoKurrent-Bold.ttf",
            "description": "./font/GoNotoKurrent-Regular.ttf",
        }
        title_font = ImageFont.truetype(font_paths["title"], 45)
        description_font = ImageFont.truetype(font_paths["description"], 22)

        draw.rectangle((200, 200, 700, 208), fill="#D7D7D7", outline=None)
        draw.rectangle(
            (200, 200, 200 + int(500 * (percentage / 100)), 208),
            fill=theme_color,
            outline=None,
        )

        draw.text(
            (560, 75),
            lang[await get_guild_language(interaction.guild.id)]["level_text"],
            font=description_font,
            fill="#e6e6e6",
        )
        draw.text((625, 57), f"{lvl}", font=title_font, fill=theme_color)

        name_font = ImageFont.truetype(font_paths["title"], 50)
        draw.text((200, 100), str(user.global_name), font=name_font, fill=theme_color)

        draw.text(
            (560, 160),
            lang[await get_guild_language(interaction.guild.id)]["level_xp"].format(
                xp=xp, totalxp=(lvl + 1) * 100
            ),
            font=description_font,
            fill="#fff",
        )

        with BytesIO() as image_binary:
            background.save(image_binary, "PNG")
            image_binary.seek(0)
            card = File(fp=image_binary, filename="rankcard.png")
            await interaction.followup.send(files=[card])

    @rank.subcommand(
        name="leaderboard",
        description="🎖️ | View the leaderboard of top ranked users!",
    )
    async def leaderboard(
        self,
        interaction: nextcord.Interaction,
        include: Optional[int] = nextcord.SlashOption(
            name="include",
            description="Select how many users you want to include on the list!",
            required=False,
        ),
    ):
        if include is None:
            include = 5

        if include < 1 or include > 50:
            await interaction.response.send_message(
                embed=Embeds.message(
                    title=lang[await get_guild_language(interaction.guild.id)][
                        class_namespace
                    ],
                    message=lang[await get_guild_language(interaction.guild.id)][
                        "leaderboard_out_of_range"
                    ],
                    message_type="warn",
                ),
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        result = await user_handler.get_leaderboard(include)

        mbed = nextcord.Embed(
            title=lang[await get_guild_language(interaction.guild.id)][
                "leaderboard_header"
            ].format(include=include),
        )

        for user_id, data in result.items():
            member = await self.bot.fetch_user(user_id)
            mbed.add_field(
                name=member.display_name,
                value=lang[await get_guild_language(interaction.guild.id)][
                    "leaderboard_user_row"
                ].format(level=data["level"], totalxp=data["totalxp"]),
                inline=False,
            )

        await interaction.followup.send(embed=mbed)


def setup(bot):
    bot.add_cog(RankSystem(bot))