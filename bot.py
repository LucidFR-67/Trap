import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timezone, timedelta
import os

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
TRAP_CHANNEL_ID = 1139160137970495538   # Your channel
KICK_REASON     = "Sent a message in a restricted channel."
WIPE_HOURS      = 1
LOG_CHANNEL_ID  = None                  # Set to a channel ID if you want logs
# ─────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def log(message: str):
    print(message)
    if LOG_CHANNEL_ID:
        ch = bot.get_channel(LOG_CHANNEL_ID)
        if ch:
            await ch.send(f"🪤 **TrapBot** | {message}")


async def delete_recent_messages(guild: discord.Guild, member: discord.Member, hours: int):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    deleted_count = 0

    for channel in guild.text_channels:
        perms = channel.permissions_for(guild.me)
        if not (perms.read_message_history and perms.manage_messages):
            continue

        try:
            to_delete = []
            async for msg in channel.history(limit=None, after=cutoff):
                if msg.author.id == member.id:
                    to_delete.append(msg)

            if to_delete:
                for i in range(0, len(to_delete), 100):
                    chunk = to_delete[i : i + 100]
                    if len(chunk) == 1:
                        await chunk[0].delete()
                    else:
                        await channel.delete_messages(chunk)
                    await asyncio.sleep(0.5)
                deleted_count += len(to_delete)

        except discord.Forbidden:
            print(f"  ⚠ No permission in #{channel.name}")
        except discord.HTTPException as e:
            print(f"  ⚠ HTTP error in #{channel.name}: {e}")

    return deleted_count


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    trap_ch = bot.get_channel(TRAP_CHANNEL_ID)
    if trap_ch:
        print(f"🪤 Trap channel: #{trap_ch.name}")
    else:
        print(f"⚠ WARNING: Trap channel not found. Check the ID.")


@bot.event
async def on_message(message: discord.Message):
    if not message.guild or message.author.bot:
        return

    if message.channel.id == TRAP_CHANNEL_ID:
        member = message.guild.get_member(message.author.id)
        if not member:
            return

        if member.top_role >= message.guild.me.top_role:
            await log(f"⚠ Cannot kick **{member}** — role too high.")
            return

        await log(f"🚨 **{member}** triggered the trap. Starting wipe + kick...")

        try:
            await message.delete()
        except discord.HTTPException:
            pass

        deleted = await delete_recent_messages(message.guild, member, WIPE_HOURS)
        await log(f"🗑 Deleted {deleted} message(s) from **{member}**.")

        try:
            await member.kick(reason=KICK_REASON)
            await log(f"👢 **{member}** has been kicked.")
        except discord.Forbidden:
            await log(f"⚠ Missing permissions to kick **{member}**.")
        except discord.HTTPException as e:
            await log(f"⚠ Failed to kick **{member}**: {e}")

    await bot.process_commands(message)


if __name__ == "__main__":
    # ⚠ REPLACE THIS with your new token after resetting it on the Discord dev portal
    token = "fa5QzC-IPxec12eCyZ13XDTbkR9aymTn"
    bot.run(token)
