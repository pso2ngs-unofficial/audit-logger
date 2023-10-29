import discord
from datetime import datetime, timedelta, timezone


# Text Channel ID for logging.
MEMBER_LOG_CHANNEL_ID = 1123497484132569148
MESSAGE_LOG_CHANNEL_ID = 1123498595828641893

# Time zone for logging.
TIMEZONE = timezone(timedelta(hours=+9), "Asia/Tokyo")

# Accent colors for embed.
COLOR_ORANGE = 0xdda353
COLOR_YELLOW = 0xd1dd53
COLOR_RED = 0xdd5e53
COLOR_BLUE = 0x4286f4


# Client
client = discord.Client(intents=discord.Intents.all(), status=discord.Status.invisible)


# Generate embed for member action logging.
def generate_member_log(entry: discord.AuditLogEntry, target: discord.User, title: str, name: str, value: str, color: int) -> str:
    embed = discord.Embed(title=title, description=target.mention, color=color, timestamp=datetime.now(TIMEZONE))
    embed.set_author(name=target.name, icon_url=target.avatar.url)
    embed.add_field(name=name, value=value, inline=False)
    if entry.reason:
        embed.add_field(name="Reason", value=entry.reason, inline=False)
    embed.set_footer(text="ID: "+ str(target.id))

    return embed


# Generate embed for message action logging.
def generate_message_log(author: discord.Member, title: str, description: str, attachments: str, message_id: str, url: str, color: int) -> str:
    embed = discord.Embed(title=title, description=description, url=url, color=color, timestamp=datetime.now(TIMEZONE))
    embed.set_author(name=author.name, icon_url=author.avatar.url)
    if attachments:
        embed.add_field(name="Attachments", value="\n".join(attachments), inline=False)
    embed.add_field(name="Message ID", value=message_id, inline=False)
    embed.set_footer(text="ID: "+ str(author.id))

    return embed


# Member Action Logging
@client.event
async def on_audit_log_entry_create(entry: discord.AuditLogEntry):
    action: discord.AuditLogAction = entry.action
    log_channel: discord.channel.TextChannel = entry.guild.get_channel(MEMBER_LOG_CHANNEL_ID)

    if action == discord.AuditLogAction.member_update:
        for (before, after) in zip(iter(entry.before), iter(entry.after)):
            before_attribute, before_value = before[0], before[1]
            after_attribute, after_value = after[0], after[1]
            
            target: discord.User = await client.fetch_user(entry.target.id)

            # Update Member Nickname
            if before_attribute == "nick":
                pass
            
            # Update Member Server Mute
            elif before_attribute == "mute":
                value = f"`{after_value}`"
                if after_value:
                    embed = generate_member_log(entry, target, "Member Server Mute", "", "", COLOR_ORANGE)
                else:
                    embed = generate_member_log(entry, target, "Member Removed From Server Mute", "", "", COLOR_YELLOW)
                
                await log_channel.send(embed=embed)

            # Update Member Server Speaker Mute
            elif before_attribute == "deaf":
                value = f"`{after_value}`"
                if after_value:
                    embed = generate_member_log(entry, target, "Member Server Speaker Mute", "", "", COLOR_ORANGE)
                else:
                    embed = generate_member_log(entry, target, "Member Removed From Server Speaker Mute", "", "", COLOR_YELLOW)

                await log_channel.send(embed=embed)

            # Update Member Timeout
            elif before_attribute == "timed_out_until":
                if type(after_value) == datetime:
                    value = f"`{after_value.replace(microsecond=0, tzinfo=TIMEZONE) + timedelta(hours=+9)}`"
                    embed = generate_member_log(entry, target, "Member Timeout", "Duration", value, COLOR_ORANGE)
                else:
                    embed = generate_member_log(entry, target, "Member Removed From Timeout", "", "", COLOR_YELLOW)
        
                await log_channel.send(embed=embed)

    if action == discord.AuditLogAction.kick:
        target: discord.User = await client.fetch_user(entry.target.id)
        embed = generate_member_log(entry, target, "Member Kicked", "", "", COLOR_RED)

        await log_channel.send(embed=embed)
        
    if action == discord.AuditLogAction.ban:
        target: discord.User = await client.fetch_user(entry.target.id)
        embed = generate_member_log(entry, target, "Member Banned", "", "", COLOR_RED)

        await log_channel.send(embed=embed)

    if action == discord.AuditLogAction.unban:
        target: discord.User = await client.fetch_user(entry.target.id)
        embed = generate_member_log(entry, target, "Member Unbanned", "", "", COLOR_BLUE)

        await log_channel.send(embed=embed)


# Message Action Logging
@client.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.author != client.user:
        title = f"Message edited in #{before.channel.name}"
        description = "**Before: **" + before.content + "\n"
        description += "**After: **" + after.content
        attachments = [f"`{att.id}/{att.filename}`" for att in before.attachments]
        message_id = f"`{before.id}`"
        url = before.jump_url

        log_channel: discord.channel.TextChannel = before.guild.get_channel(MESSAGE_LOG_CHANNEL_ID)
        embed = generate_message_log(before.author, title, description, attachments, message_id, url, COLOR_BLUE)
        await log_channel.send(embed=embed)

@client.event
async def on_message_delete(message: discord.Message):
    if message.author != client.user:
        title = f"Message deleted in #{message.channel.name}"
        description = "**Before: **" + message.content + "\n"
        description += "**After: **"
        attachments = [f"`{att.id}/{att.filename}`" for att in message.attachments]
        message_id = f"`{message.id}`"
        url = ""

        log_channel: discord.channel.TextChannel = message.guild.get_channel(MESSAGE_LOG_CHANNEL_ID)
        embed = generate_message_log(message.author, title, description, attachments, message_id, url, COLOR_RED)
        await log_channel.send(embed=embed)


# Client Run
with open(".token", "r") as token:
    client.run(token.read())
    