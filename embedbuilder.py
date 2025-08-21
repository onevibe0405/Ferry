import discord
from discord.ui import View, Button, Modal, TextInput
from discord import Interaction
from datetime import datetime
from utils import replace_placeholders, save_data  # adjust import if needed

class EmbedBuilderView(View):
    def __init__(self, bot, ctx, name: str):
        super().__init__(timeout=600)
        self.bot = bot
        self.ctx = ctx
        self.name = name
        self.embed = discord.Embed(title="New Embed", description="Describe here...", color=discord.Color.blue())
        self.timestamp_enabled = False

        # Raw fields to keep placeholders
        self.raw_title = ""
        self.raw_description = ""
        self.raw_color = None
        self.raw_thumbnail = ""
        self.raw_image = ""
        self.raw_footer = ""
        self.raw_author_name = ""
        self.raw_author_icon = ""

    @discord.ui.button(label="📝 Content", style=discord.ButtonStyle.primary)
    async def content_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(EmbedContentModal(self))

    @discord.ui.button(label="🖼 Thumbnail", style=discord.ButtonStyle.secondary)
    async def thumbnail_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(SimpleModal(self, "Thumbnail URL", "thumbnail"))

    @discord.ui.button(label="🖼 Image", style=discord.ButtonStyle.secondary)
    async def image_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(SimpleModal(self, "Image URL", "image"))

    @discord.ui.button(label="✏ Footer", style=discord.ButtonStyle.success)
    async def footer_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(SimpleModal(self, "Footer text", "footer"))

    @discord.ui.button(label="👤 Author", style=discord.ButtonStyle.success)
    async def author_button(self, interaction: Interaction, button: Button):
        await interaction.response.send_modal(AuthorModal(self))

    @discord.ui.button(label="⏱ Toggle Timestamp", style=discord.ButtonStyle.secondary)
    async def timestamp_button(self, interaction: Interaction, button: Button):
        self.timestamp_enabled = not self.timestamp_enabled
        self.embed.timestamp = datetime.utcnow() if self.timestamp_enabled else None
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="✅ Finish & Save", style=discord.ButtonStyle.green)
    async def finish_button(self, interaction: Interaction, button: Button):
        guild_id = str(interaction.guild.id)
        # Save raw placeholders, not replaced text
        self.bot.data.setdefault('embeds', {}).setdefault(guild_id, {})[self.name] = {
            'title': self.raw_title,
            'description': self.raw_description,
            'color': self.raw_color,
            'thumbnail': self.raw_thumbnail,
            'image': self.raw_image,
            'footer': self.raw_footer,
            'author': {
                'name': self.raw_author_name,
                'icon_url': self.raw_author_icon
            },
            'timestamp': self.timestamp_enabled
        }
        save_data(self.bot.data)
                
        # Force reload data to ensure sync
        from utils import load_data
        self.bot.data = load_data()
        
        await interaction.response.edit_message(content=f"✅ Embed `{self.name}` saved!", embed=None, view=None)

# -----------------------------

class EmbedContentModal(Modal):
    def __init__(self, view: EmbedBuilderView):
        super().__init__(title="📝 Edit Embed Content")
        self.view = view

        # Use raw values if editing again
        self.title_input = TextInput(
            label="Title", 
            default=view.raw_title or "",
            required=False, max_length=256)
        self.desc_input = TextInput(
            label="Description", 
            default=view.raw_description or "",
            required=False, style=discord.TextStyle.paragraph)
        self.color_input = TextInput(
            label="Color (hex, e.g. FF5733)", 
            default=view.raw_color or "", 
            required=False, max_length=6)

        self.add_item(self.title_input)
        self.add_item(self.desc_input)
        self.add_item(self.color_input)

    async def on_submit(self, interaction: Interaction):
        user = self.view.ctx.author
        bot_user = self.view.ctx.bot.user
        guild = self.view.ctx.guild
        channel = self.view.ctx.channel

        # Save raw
        self.view.raw_title = self.title_input.value or ""
        self.view.raw_description = self.desc_input.value or ""
        self.view.raw_color = self.color_input.value.strip().lstrip('#') if self.color_input.value else None

        # Replace placeholders for preview
        title = replace_placeholders(self.view.raw_title, user=user, bot=bot_user, guild=guild, channel=channel) or None
        description = replace_placeholders(self.view.raw_description, user=user, bot=bot_user, guild=guild, channel=channel) or None

        color = None
        if self.view.raw_color:
            try:
                color = int(self.view.raw_color, 16)
            except ValueError:
                await interaction.response.send_message("❌ Invalid hex color!", ephemeral=True)
                return

        # Update embed
        self.view.embed.title = title
        self.view.embed.description = description
        if color is not None:
            self.view.embed.color = discord.Color(color)

        await interaction.response.edit_message(embed=self.view.embed, view=self.view)

# -----------------------------

class SimpleModal(Modal):
    def __init__(self, view: EmbedBuilderView, label: str, field: str):
        super().__init__(title=f"Edit {label}")
        self.view = view
        self.field = field
        self.input = TextInput(label=label, required=True, max_length=512)
        self.add_item(self.input)

    async def on_submit(self, interaction: Interaction):
        user = self.view.ctx.author
        bot_user = self.view.ctx.bot.user
        guild = self.view.ctx.guild
        channel = self.view.ctx.channel

        raw = self.input.value or ""

        # Save raw & replace for preview
        value = replace_placeholders(raw, user=user, bot=bot_user, guild=guild, channel=channel)

        if self.field == "footer":
            self.view.raw_footer = raw
            self.view.embed.set_footer(text=value)
        elif self.field == "thumbnail":
            self.view.raw_thumbnail = raw
            self.view.embed.set_thumbnail(url=value)
        elif self.field == "image":
            self.view.raw_image = raw
            self.view.embed.set_image(url=value)

        await interaction.response.edit_message(embed=self.view.embed, view=self.view)

# -----------------------------

class AuthorModal(Modal):
    def __init__(self, view: EmbedBuilderView):
        super().__init__(title="👤 Set Author")
        self.view = view
        self.name_input = TextInput(label="Author name", default=view.raw_author_name or "", required=True, max_length=256)
        self.icon_input = TextInput(label="Author icon URL (optional)", default=view.raw_author_icon or "", required=False)
        self.add_item(self.name_input)
        self.add_item(self.icon_input)

    async def on_submit(self, interaction: Interaction):
        user = self.view.ctx.author
        bot_user = self.view.ctx.bot.user
        guild = self.view.ctx.guild
        channel = self.view.ctx.channel

        self.view.raw_author_name = self.name_input.value or ""
        self.view.raw_author_icon = self.icon_input.value or ""

        name = replace_placeholders(self.view.raw_author_name, user=user, bot=bot_user, guild=guild, channel=channel) or None
        icon = replace_placeholders(self.view.raw_author_icon, user=user, bot=bot_user, guild=guild, channel=channel) if self.view.raw_author_icon else None

        self.view.embed.set_author(name=name, icon_url=icon)
        await interaction.response.edit_message(embed=self.view.embed, view=self.view)
