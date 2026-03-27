import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

# ============================================================
#  ΡΥΘΜΙΣΕΙΣ — Βαλε μονο το token σου εδω
# ============================================================

# ── Database ─────────────────────────────────────────────────
def db_connect():
    return sqlite3.connect("servers.db")

def db_init():
    with db_connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS server_config (
                guild_id      INTEGER PRIMARY KEY,
                welcome_ch    INTEGER DEFAULT 0,
                leave_ch      INTEGER DEFAULT 0,
                log_msg_ch    INTEGER DEFAULT 0,
                log_voice_ch  INTEGER DEFAULT 0,
                log_channel_ch INTEGER DEFAULT 0,
                log_role_ch   INTEGER DEFAULT 0,
                log_mod_ch    INTEGER DEFAULT 0,
                mod_role      INTEGER DEFAULT 0
            )
        """)
db_init()

def get_config(guild_id: int) -> dict:
    with db_connect() as con:
        row = con.execute(
            """SELECT welcome_ch, leave_ch, log_msg_ch, log_voice_ch,
                      log_channel_ch, log_role_ch, log_mod_ch, mod_role
               FROM server_config WHERE guild_id=?""",
            (guild_id,)
        ).fetchone()
    if row:
        keys = ["welcome_ch","leave_ch","log_msg_ch","log_voice_ch",
                "log_channel_ch","log_role_ch","log_mod_ch","mod_role"]
        return dict(zip(keys, row))
    return {k: 0 for k in ["welcome_ch","leave_ch","log_msg_ch","log_voice_ch",
                            "log_channel_ch","log_role_ch","log_mod_ch","mod_role"]}

def set_config(guild_id: int, **kwargs):
    cfg = get_config(guild_id)
    cfg.update(kwargs)
    with db_connect() as con:
        con.execute("""
            INSERT INTO server_config
                (guild_id, welcome_ch, leave_ch, log_msg_ch, log_voice_ch,
                 log_channel_ch, log_role_ch, log_mod_ch, mod_role)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(guild_id) DO UPDATE SET
                welcome_ch=excluded.welcome_ch,
                leave_ch=excluded.leave_ch,
                log_msg_ch=excluded.log_msg_ch,
                log_voice_ch=excluded.log_voice_ch,
                log_channel_ch=excluded.log_channel_ch,
                log_role_ch=excluded.log_role_ch,
                log_mod_ch=excluded.log_mod_ch,
                mod_role=excluded.mod_role
        """, (guild_id,
              cfg["welcome_ch"], cfg["leave_ch"],
              cfg["log_msg_ch"], cfg["log_voice_ch"],
              cfg["log_channel_ch"], cfg["log_role_ch"],
              cfg["log_mod_ch"], cfg["mod_role"]))

# ── Βοηθητικες ───────────────────────────────────────────────
async def send_log(guild: discord.Guild, log_key: str, embed: discord.Embed):
    """Στελνει embed στο αντιστοιχο log channel βασει log_key."""
    cfg = get_config(guild.id)
    ch = guild.get_channel(cfg[log_key])
    if ch:
        await ch.send(embed=embed)

async def mod_check(interaction: discord.Interaction) -> bool:
    cfg = get_config(interaction.guild_id)
    mod_role = interaction.guild.get_role(cfg["mod_role"])
    if interaction.user.guild_permissions.administrator:
        return True
    if mod_role and mod_role in interaction.user.roles:
        return True
    await interaction.response.send_message(
        "❌ Δεν έχεις δικαίωμα να χρησιμοποιήσεις αυτή την εντολή.", ephemeral=True
    )
    return False

# ── Bot ──────────────────────────────────────────────────────
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


# ════════════════════════════════════════════════════════════
#  ON READY
# ════════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    await tree.sync()
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name=f"/help | {len(bot.guilds)} servers"
    ))
    print(f"✅  Bot online ως {bot.user}  |  {len(bot.guilds)} server(s)")
    print("📡  Slash commands synced!")


# ════════════════════════════════════════════════════════════
#  SETUP GROUP
# ════════════════════════════════════════════════════════════
setup_group = app_commands.Group(name="setup", description="Ρύθμιση bot για τον server σου")

@setup_group.command(name="welcome", description="Κανάλι καλωσορίσματος")
@app_commands.checks.has_permissions(administrator=True)
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    set_config(interaction.guild_id, welcome_ch=channel.id)
    await interaction.response.send_message(f"✅ Welcome κανάλι: {channel.mention}", ephemeral=True)

@setup_group.command(name="leave", description="Κανάλι αποχώρησης")
@app_commands.checks.has_permissions(administrator=True)
async def setup_leave(interaction: discord.Interaction, channel: discord.TextChannel):
    set_config(interaction.guild_id, leave_ch=channel.id)
    await interaction.response.send_message(f"✅ Leave κανάλι: {channel.mention}", ephemeral=True)

@setup_group.command(name="log_messages", description="Log κανάλι για μηνύματα (delete/edit)")
@app_commands.checks.has_permissions(administrator=True)
async def setup_log_msg(interaction: discord.Interaction, channel: discord.TextChannel):
    set_config(interaction.guild_id, log_msg_ch=channel.id)
    await interaction.response.send_message(f"✅ Message logs: {channel.mention}", ephemeral=True)

@setup_group.command(name="log_voice", description="Log κανάλι για voice (join/leave/move)")
@app_commands.checks.has_permissions(administrator=True)
async def setup_log_voice(interaction: discord.Interaction, channel: discord.TextChannel):
    set_config(interaction.guild_id, log_voice_ch=channel.id)
    await interaction.response.send_message(f"✅ Voice logs: {channel.mention}", ephemeral=True)

@setup_group.command(name="log_channels", description="Log κανάλι για κανάλια (create/delete)")
@app_commands.checks.has_permissions(administrator=True)
async def setup_log_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    set_config(interaction.guild_id, log_channel_ch=channel.id)
    await interaction.response.send_message(f"✅ Channel logs: {channel.mention}", ephemeral=True)

@setup_group.command(name="log_roles", description="Log κανάλι για ρόλους (create/delete/αλλαγές)")
@app_commands.checks.has_permissions(administrator=True)
async def setup_log_role(interaction: discord.Interaction, channel: discord.TextChannel):
    set_config(interaction.guild_id, log_role_ch=channel.id)
    await interaction.response.send_message(f"✅ Role logs: {channel.mention}", ephemeral=True)

@setup_group.command(name="log_mod", description="Log κανάλι για moderation (kick/ban/mute/warn)")
@app_commands.checks.has_permissions(administrator=True)
async def setup_log_mod(interaction: discord.Interaction, channel: discord.TextChannel):
    set_config(interaction.guild_id, log_mod_ch=channel.id)
    await interaction.response.send_message(f"✅ Moderation logs: {channel.mention}", ephemeral=True)

@setup_group.command(name="modrole", description="Ρόλος moderator")
@app_commands.checks.has_permissions(administrator=True)
async def setup_modrole(interaction: discord.Interaction, role: discord.Role):
    set_config(interaction.guild_id, mod_role=role.id)
    await interaction.response.send_message(f"✅ Mod role: {role.mention}", ephemeral=True)

@setup_group.command(name="show", description="Δείχνει τις τρέχουσες ρυθμίσεις")
@app_commands.checks.has_permissions(administrator=True)
async def setup_show(interaction: discord.Interaction):
    cfg = get_config(interaction.guild_id)
    g = interaction.guild
    def ch(cid): return g.get_channel(cid).mention if g.get_channel(cid) else "❌ Δεν έχει οριστεί"
    def ro(rid): return g.get_role(rid).mention    if g.get_role(rid)    else "❌ Δεν έχει οριστεί"

    embed = discord.Embed(title="⚙️  Ρυθμίσεις Server", color=discord.Color.blurple(), timestamp=datetime.utcnow())
    embed.add_field(name="👋 Welcome",          value=ch(cfg["welcome_ch"]),    inline=True)
    embed.add_field(name="🚪 Leave",            value=ch(cfg["leave_ch"]),      inline=True)
    embed.add_field(name="\u200b",              value="\u200b",                 inline=True)
    embed.add_field(name="📝 Log Μηνυμάτων",   value=ch(cfg["log_msg_ch"]),    inline=True)
    embed.add_field(name="🎙️ Log Voice",        value=ch(cfg["log_voice_ch"]),  inline=True)
    embed.add_field(name="📁 Log Καναλιών",     value=ch(cfg["log_channel_ch"]),inline=True)
    embed.add_field(name="🎭 Log Ρόλων",        value=ch(cfg["log_role_ch"]),   inline=True)
    embed.add_field(name="🛡️ Log Moderation",   value=ch(cfg["log_mod_ch"]),    inline=True)
    embed.add_field(name="🔑 Mod Role",         value=ro(cfg["mod_role"]),      inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

tree.add_command(setup_group)


# ════════════════════════════════════════════════════════════
#  WELCOME & LEAVE
# ════════════════════════════════════════════════════════════
@bot.event
async def on_member_join(member: discord.Member):
    cfg = get_config(member.guild.id)
    channel = member.guild.get_channel(cfg["welcome_ch"])
    if not channel: return
    embed = discord.Embed(
        title="👋  Καλωσόρισες!",
        description=(
            f"Χαιρετίσματα {member.mention}!\n\n"
            f"Είσαι το **{member.guild.member_count}ο** μέλος του **{member.guild.name}**.\n"
            f"Διάβασε τους κανόνες και απόλαυσε!"
        ),
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_image(url=member.display_avatar.url)
    embed.set_footer(text=member.guild.name,
                     icon_url=member.guild.icon.url if member.guild.icon else None)
    await channel.send(embed=embed)

@bot.event
async def on_member_remove(member: discord.Member):
    cfg = get_config(member.guild.id)
    channel = member.guild.get_channel(cfg["leave_ch"])
    if not channel: return
    embed = discord.Embed(
        title="🚪  Αποχώρηση",
        description=(
            f"Ο/Η **{member}** έφυγε από τον server.\n"
            f"Τώρα είμαστε **{member.guild.member_count}** μέλη."
        ),
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=member.guild.name,
                     icon_url=member.guild.icon.url if member.guild.icon else None)
    await channel.send(embed=embed)


# ════════════════════════════════════════════════════════════
#  MODERATION SLASH COMMANDS
# ════════════════════════════════════════════════════════════
@tree.command(name="kick", description="Κάνει kick ένα μέλος")
@app_commands.describe(member="Το μέλος", reason="Ο λόγος")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Δεν δόθηκε λόγος"):
    if not await mod_check(interaction): return
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Δεν μπορείς να κάνεις kick αυτό το μέλος.", ephemeral=True); return
    await member.kick(reason=reason)
    embed = discord.Embed(title="👢  Kick", color=discord.Color.orange(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Χρήστης", value=f"{member} (`{member.id}`)", inline=True)
    embed.add_field(name="Από",     value=str(interaction.user), inline=True)
    embed.add_field(name="Λόγος",   value=reason, inline=False)
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, "log_mod_ch", embed)

@tree.command(name="ban", description="Κάνει ban ένα μέλος")
@app_commands.describe(member="Το μέλος", reason="Ο λόγος")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Δεν δόθηκε λόγος"):
    if not await mod_check(interaction): return
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Δεν μπορείς να κάνεις ban αυτό το μέλος.", ephemeral=True); return
    await member.ban(reason=reason)
    embed = discord.Embed(title="🔨  Ban", color=discord.Color.dark_red(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Χρήστης", value=f"{member} (`{member.id}`)", inline=True)
    embed.add_field(name="Από",     value=str(interaction.user), inline=True)
    embed.add_field(name="Λόγος",   value=reason, inline=False)
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, "log_mod_ch", embed)

@tree.command(name="unban", description="Κάνει unban χρήστη με ID")
@app_commands.describe(user_id="Το Discord ID του χρήστη")
async def unban(interaction: discord.Interaction, user_id: str):
    if not await mod_check(interaction): return
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        embed = discord.Embed(title="✅  Unban", color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.add_field(name="Χρήστης", value=str(user), inline=True)
        embed.add_field(name="Από",     value=str(interaction.user), inline=True)
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, "log_mod_ch", embed)
    except (discord.NotFound, ValueError):
        await interaction.response.send_message("❌ Δεν βρέθηκε.", ephemeral=True)

@tree.command(name="mute", description="Κάνει mute ένα μέλος")
@app_commands.describe(member="Το μέλος", reason="Ο λόγος")
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = "Δεν δόθηκε λόγος"):
    if not await mod_check(interaction): return
    mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if not mute_role:
        mute_role = await interaction.guild.create_role(name="Muted", reason="Auto-created by bot")
        for ch in interaction.guild.channels:
            await ch.set_permissions(mute_role, send_messages=False, speak=False, add_reactions=False)
    await member.add_roles(mute_role, reason=reason)
    embed = discord.Embed(title="🔇  Mute", color=discord.Color.greyple(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Χρήστης", value=str(member), inline=True)
    embed.add_field(name="Από",     value=str(interaction.user), inline=True)
    embed.add_field(name="Λόγος",   value=reason, inline=False)
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, "log_mod_ch", embed)

@tree.command(name="unmute", description="Κάνει unmute ένα μέλος")
@app_commands.describe(member="Το μέλος")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if not await mod_check(interaction): return
    mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if mute_role and mute_role in member.roles:
        await member.remove_roles(mute_role)
        embed = discord.Embed(title="🔊  Unmute", color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.add_field(name="Χρήστης", value=str(member), inline=True)
        embed.add_field(name="Από",     value=str(interaction.user), inline=True)
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, "log_mod_ch", embed)
    else:
        await interaction.response.send_message("❌ Ο χρήστης δεν είναι muted.", ephemeral=True)

@tree.command(name="warn", description="Προειδοποιεί ένα μέλος")
@app_commands.describe(member="Το μέλος", reason="Ο λόγος")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "Δεν δόθηκε λόγος"):
    if not await mod_check(interaction): return
    embed = discord.Embed(title="⚠️  Προειδοποίηση", color=discord.Color.yellow(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Χρήστης", value=str(member), inline=True)
    embed.add_field(name="Από",     value=str(interaction.user), inline=True)
    embed.add_field(name="Λόγος",   value=reason, inline=False)
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, "log_mod_ch", embed)
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        pass

@tree.command(name="clear", description="Διαγράφει μηνύματα από το κανάλι")
@app_commands.describe(amount="Πόσα μηνύματα (1–100)")
async def clear(interaction: discord.Interaction, amount: int = 10):
    if not await mod_check(interaction): return
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ Δώσε αριθμό 1–100.", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ Διαγράφηκαν **{len(deleted)}** μηνύματα.", ephemeral=True)

@tree.command(name="addrole", description="Δίνει ρόλο σε μέλος")
@app_commands.describe(member="Το μέλος", role="Ο ρόλος")
async def addrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not await mod_check(interaction): return
    await member.add_roles(role)
    await interaction.response.send_message(f"✅ Δόθηκε ο ρόλος **{role.name}** στον **{member}**.")

@tree.command(name="removerole", description="Αφαιρεί ρόλο από μέλος")
@app_commands.describe(member="Το μέλος", role="Ο ρόλος")
async def removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not await mod_check(interaction): return
    await member.remove_roles(role)
    await interaction.response.send_message(f"✅ Αφαιρέθηκε ο ρόλος **{role.name}** από τον **{member}**.")


# ════════════════════════════════════════════════════════════
#  LOGS — 📝 Μηνύματα  →  log_msg_ch
# ════════════════════════════════════════════════════════════
@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot or not message.guild: return
    embed = discord.Embed(title="🗑️  Μήνυμα Διαγράφηκε", color=discord.Color.red(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=message.author.display_avatar.url)
    embed.add_field(name="Χρήστης",      value=f"{message.author} (`{message.author.id}`)", inline=True)
    embed.add_field(name="Κανάλι",       value=message.channel.mention, inline=True)
    embed.add_field(name="Περιεχόμενο", value=message.content[:1020] or "*[χωρίς κείμενο]*", inline=False)
    await send_log(message.guild, "log_msg_ch", embed)

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.author.bot or not before.guild: return
    if before.content == after.content: return
    embed = discord.Embed(title="✏️  Μήνυμα Επεξεργάστηκε", color=discord.Color.blue(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=before.author.display_avatar.url)
    embed.add_field(name="Χρήστης", value=f"{before.author} (`{before.author.id}`)", inline=True)
    embed.add_field(name="Κανάλι",  value=before.channel.mention, inline=True)
    embed.add_field(name="Πριν",    value=before.content[:1020] or "*[κενό]*", inline=False)
    embed.add_field(name="Μετά",    value=after.content[:1020]  or "*[κενό]*", inline=False)
    embed.add_field(name="🔗 Link", value=f"[Πήγαινε στο μήνυμα]({after.jump_url})", inline=False)
    await send_log(before.guild, "log_msg_ch", embed)


# ════════════════════════════════════════════════════════════
#  LOGS — 🎙️ Voice  →  log_voice_ch
# ════════════════════════════════════════════════════════════
@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot: return
    embed = None
    if not before.channel and after.channel:
        embed = discord.Embed(title="🎙️  Μπήκε σε Voice", color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.add_field(name="Χρήστης", value=str(member), inline=True)
        embed.add_field(name="Κανάλι",  value=after.channel.name, inline=True)
    elif before.channel and not after.channel:
        embed = discord.Embed(title="🔇  Έφυγε από Voice", color=discord.Color.red(), timestamp=datetime.utcnow())
        embed.add_field(name="Χρήστης", value=str(member), inline=True)
        embed.add_field(name="Κανάλι",  value=before.channel.name, inline=True)
    elif before.channel and after.channel and before.channel != after.channel:
        embed = discord.Embed(title="🔀  Μετακινήθηκε σε Voice", color=discord.Color.blurple(), timestamp=datetime.utcnow())
        embed.add_field(name="Χρήστης", value=str(member), inline=False)
        embed.add_field(name="Από",     value=before.channel.name, inline=True)
        embed.add_field(name="Σε",      value=after.channel.name,  inline=True)
    if embed:
        embed.set_thumbnail(url=member.display_avatar.url)
        await send_log(member.guild, "log_voice_ch", embed)


# ════════════════════════════════════════════════════════════
#  LOGS — 📁 Κανάλια  →  log_channel_ch
# ════════════════════════════════════════════════════════════
@bot.event
async def on_guild_channel_create(channel):
    embed = discord.Embed(title="📁  Κανάλι Δημιουργήθηκε", color=discord.Color.green(), timestamp=datetime.utcnow())
    embed.add_field(name="Όνομα", value=channel.name, inline=True)
    embed.add_field(name="Τύπος", value=str(channel.type).capitalize(), inline=True)
    if hasattr(channel, "category") and channel.category:
        embed.add_field(name="Κατηγορία", value=channel.category.name, inline=True)
    await send_log(channel.guild, "log_channel_ch", embed)

@bot.event
async def on_guild_channel_delete(channel):
    embed = discord.Embed(title="🗑️  Κανάλι Διαγράφηκε", color=discord.Color.red(), timestamp=datetime.utcnow())
    embed.add_field(name="Όνομα", value=channel.name, inline=True)
    embed.add_field(name="Τύπος", value=str(channel.type).capitalize(), inline=True)
    await send_log(channel.guild, "log_channel_ch", embed)


# ════════════════════════════════════════════════════════════
#  LOGS — 🎭 Ρόλοι  →  log_role_ch
# ════════════════════════════════════════════════════════════
@bot.event
async def on_guild_role_create(role: discord.Role):
    embed = discord.Embed(title="🎭  Ρόλος Δημιουργήθηκε", color=discord.Color.green(), timestamp=datetime.utcnow())
    embed.add_field(name="Όνομα", value=role.name,     inline=True)
    embed.add_field(name="ID",    value=str(role.id),  inline=True)
    embed.add_field(name="Χρώμα", value=str(role.color), inline=True)
    await send_log(role.guild, "log_role_ch", embed)

@bot.event
async def on_guild_role_delete(role: discord.Role):
    embed = discord.Embed(title="🗑️  Ρόλος Διαγράφηκε", color=discord.Color.red(), timestamp=datetime.utcnow())
    embed.add_field(name="Όνομα", value=role.name,    inline=True)
    embed.add_field(name="ID",    value=str(role.id), inline=True)
    await send_log(role.guild, "log_role_ch", embed)

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    added   = [r for r in after.roles  if r not in before.roles]
    removed = [r for r in before.roles if r not in after.roles]
    if not added and not removed: return
    embed = discord.Embed(title="👤  Αλλαγή Ρόλων Μέλους", color=discord.Color.blue(), timestamp=datetime.utcnow())
    embed.set_thumbnail(url=after.display_avatar.url)
    embed.add_field(name="Χρήστης", value=f"{after} (`{after.id}`)", inline=False)
    if added:   embed.add_field(name="➕ Προστέθηκε", value=" ".join(r.mention for r in added),   inline=True)
    if removed: embed.add_field(name="➖ Αφαιρέθηκε", value=" ".join(r.mention for r in removed), inline=True)
    await send_log(after.guild, "log_role_ch", embed)


# ════════════════════════════════════════════════════════════
#  HELP
# ════════════════════════════════════════════════════════════
@tree.command(name="help", description="Δείχνει όλες τις εντολές")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖  Εντολές Bot",
        description="Χρησιμοποίησε `/setup` για να ρυθμίσεις τον server σου (απαιτείται Administrator).",
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(
        name="⚙️  Setup (Administrator)",
        value=(
            "`/setup welcome`      — Κανάλι καλωσορίσματος\n"
            "`/setup leave`        — Κανάλι αποχώρησης\n"
            "`/setup log_messages` — Log μηνυμάτων\n"
            "`/setup log_voice`    — Log voice\n"
            "`/setup log_channels` — Log καναλιών\n"
            "`/setup log_roles`    — Log ρόλων\n"
            "`/setup log_mod`      — Log moderation\n"
            "`/setup modrole`      — Mod role\n"
            "`/setup show`         — Δείχνει ρυθμίσεις"
        ),
        inline=False
    )
    embed.add_field(
        name="🛡️  Moderation (Mod Role)",
        value="`/kick` `/ban` `/unban` `/mute` `/unmute` `/warn` `/clear` `/addrole` `/removerole`",
        inline=False
    )
    embed.add_field(
        name="📋  Αυτόματα Logs",
        value=(
            "📝 `log_messages` → delete / edit μηνυμάτων\n"
            "🎙️ `log_voice`    → join / leave / move\n"
            "📁 `log_channels` → create / delete καναλιών\n"
            "🎭 `log_roles`    → create / delete ρόλων + αλλαγές μελών\n"
            "🛡️ `log_mod`      → kick / ban / mute / warn"
        ),
        inline=False
    )
    embed.set_footer(
        text=interaction.guild.name,
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ════════════════════════════════════════════════════════════
#  ΕΚΚΙΝΗΣΗ
# ════════════════════════════════════════════════════════════
bot.run(TOKEN)