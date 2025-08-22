"""
Fun Commands for Discord Bot
Contains games, jokes, facts, ship, dice, 8ball, and other entertainment commands
"""

import discord
from discord.ext import commands
from discord import app_commands
import random
from utils import create_embed, get_emoji, parse_time

@commands.hybrid_command(name='ship', with_app_command=True, description='Ship two users and get love percentage!')
@app_commands.describe(user1='First user', user2='Second user (optional)')
async def ship(ctx, user1: discord.Member, user2: discord.Member = None):
    try:
        # Default to author as second user if not provided
        if user2 is None:
            user2 = ctx.author

        bot_user = ctx.bot.user
        owner_id = 957110332495630366  # Your user ID

        # Check special case: if bot is being shipped
        if bot_user in (user1, user2):
            other = user2 if user1 == bot_user else user1

            if other.id == owner_id:
                # If owner ships with bot
                percentage = 100
                message = "A match made in heaven! 💍"
            else:
                # If anyone else ships with bot
                embed = create_embed(
                    "💔 Forbidden Ship",
                    "Stay away! I'm made for Onevibe 💢",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)
        else:
            # Normal logic
            combined_id = str(user1.id) + str(user2.id)
            random.seed(hash(combined_id))
            percentage = random.randint(0, 100)

            if percentage >= 90:
                message = "Perfect match! 💕"
            elif percentage >= 70:
                message = "Great compatibility! 💖"
            elif percentage >= 50:
                message = "Good potential! 💓"
            elif percentage >= 30:
                message = "Could work with effort! 💗"
            else:
                message = "Better as friends! 💙"

        # Heart bar
        filled_hearts = "💖" * (percentage // 10)
        empty_hearts = "🤍" * (10 - (percentage // 10))
        heart_bar = filled_hearts + empty_hearts

        # Send embed
        embed = create_embed(
            "💕 Love Calculator",
            f"**{user1.display_name}** + **{user2.display_name}**\n\n"
            f"**Compatibility:** {percentage}%\n"
            f"{heart_bar}\n\n"
            f"*{message}*",
            color=discord.Color.pink()
        )
        await ctx.send(embed=embed)

    except Exception as e:
        print(f"❌ Ship command error: {e}")
        import traceback; traceback.print_exc()
        await ctx.send(f"❌ Error: `{e}`")

@commands.hybrid_command(name='coinflip', description='Flip a coin')
async def coinflip(ctx):
    result = random.choice(['Heads', 'Tails'])
    embed = create_embed("🪙 Coin Flip", f"The coin landed on: **{result}**")
    await ctx.send(embed=embed)

@commands.hybrid_command(name='dice', description='Roll a dice')
@app_commands.describe(sides='Number of sides on the dice (2-100)')
async def dice(ctx, sides: int = 6):
    if sides < 2 or sides > 100:
        embed = create_embed(f"{get_emoji('cross')} Invalid Dice", "Dice must have 2-100 sides!")
        return await ctx.send(embed=embed)
    
    result = random.randint(1, sides)
    embed = create_embed("🎲 Dice Roll", f"Rolling a {sides}-sided dice...\nResult: **{result}**")
    await ctx.send(embed=embed)

@commands.hybrid_command(name='8ball', description='Ask the magic 8-ball')
@app_commands.describe(question='Your question')
async def eightball(ctx, *, question: str):
    responses = [
        "It is certain", "Without a doubt", "Yes, definitely", "You may rely on it",
        "As I see it, yes", "Most likely", "Outlook good", "Yes", "Signs point to yes",
        "Reply hazy, try again", "Ask again later", "Better not tell you now",
        "Cannot predict now", "Concentrate and ask again", "Don't count on it",
        "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"
    ]
    
    response = random.choice(responses)
    embed = create_embed("🎱 Magic 8-Ball", f"**Question:** {question}\n**Answer:** {response}")
    await ctx.send(embed=embed)

@commands.hybrid_command(name='joke', description='Get a random joke')
async def joke(ctx):
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "Why did the scarecrow win an award? He was outstanding in his field!",
        "Why don't eggs tell jokes? They'd crack each other up!",
        "What do you call a fake noodle? An impasta!",
        "Why did the math book look so sad? Because it was full of problems!"
    ]
    
    joke_text = random.choice(jokes)
    embed = create_embed("😂 Random Joke", joke_text)
    await ctx.send(embed=embed)

@commands.hybrid_command(name='fact', description='Get a random fact')
async def fact(ctx):
    facts = [
        "Honey never spoils. Archaeologists have found edible honey in ancient Egyptian tombs!",
        "A group of flamingos is called a 'flamboyance'.",
        "Bananas are berries, but strawberries aren't!",
        "The shortest war in history lasted only 38-45 minutes.",
        "Octopuses have three hearts and blue blood!"
    ]
    
    fact_text = random.choice(facts)
    embed = create_embed("📖 Random Fact", fact_text)
    await ctx.send(embed=embed)

@commands.hybrid_command(name='poll', description='Create a poll')
@app_commands.describe(question='Poll question', options='Poll options separated by | (max 10)')
async def poll(ctx, question: str, *, options: str):
    option_list = [opt.strip() for opt in options.split('|')]
    
    if len(option_list) < 2:
        embed = create_embed(f"{get_emoji('cross')} Invalid Poll", "You need at least 2 options!")
        return await ctx.send(embed=embed)
    
    if len(option_list) > 10:
        embed = create_embed(f"{get_emoji('cross')} Too Many Options", "Maximum 10 options allowed!")
        return await ctx.send(embed=embed)
    
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    
    description = f"**{question}**\n\n"
    for i, option in enumerate(option_list):
        description += f"{reactions[i]} {option}\n"
    
    embed = create_embed("📊 Poll", description)
    message = await ctx.send(embed=embed)
    
    for i in range(len(option_list)):
        await message.add_reaction(reactions[i])

@commands.hybrid_command(name='remind', description='Set a reminder')
@app_commands.describe(time='Time to remind (e.g., 10m, 1h)', message='Reminder message')
async def remind(ctx, time: str, *, message: str = "Reminder"):
    duration = parse_time(time)
    if not duration:
        embed = create_embed(f"{get_emoji('cross')} Invalid Time", "Use format like: 10m, 1h, 2d")
        return await ctx.send(embed=embed)
    
    embed = create_embed(
        f"{get_emoji('tick')} Reminder Set",
        f"I'll remind you about: **{message}**\nIn: **{time}**"
    )
    await ctx.send(embed=embed)

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(label="‎ ", style=discord.ButtonStyle.secondary, row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToe = self.view
        state = view.board[self.y][self.x]
        if state != 0:
            return await interaction.response.send_message("That spot is already taken!", ephemeral=True)

        if view.current_player != interaction.user:
            return await interaction.response.send_message("It's not your turn!", ephemeral=True)

        # Set board state
        if view.current_player == view.player1:
            self.style = discord.ButtonStyle.danger
            self.label = "X"
            view.board[self.y][self.x] = 1
            view.current_player = view.player2
        else:
            self.style = discord.ButtonStyle.success
            self.label = "O"
            view.board[self.y][self.x] = 2
            view.current_player = view.player1

        self.disabled = True

        winner = view.check_winner()
        if winner is not None:
            for child in view.children:
                child.disabled = True
            if winner == 0:
                embed = create_embed(title="Tic Tac Toe", description="**It's a draw!**")
            else:
                embed = create_embed(
                    title="Tic Tac Toe",
                    description=f"**{view.player1.mention if winner == 1 else view.player2.mention} wins!**"
                )
            await interaction.response.edit_message(embed=embed, view=view)
            view.stop()
            return

        embed = create_embed(
            title="Tic Tac Toe",
            description=(
                f"**{view.player1.mention} (X)** vs **{view.player2.mention} (O)**\n"
                f"**{view.current_player.mention}'s turn**"
            )
        )
        await interaction.response.edit_message(embed=embed, view=view)

class TicTacToe(discord.ui.View):
    def __init__(self, player1, player2):
        super().__init__()
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.board = [[0] * 3 for _ in range(3)]

        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_winner(self):
        # Check rows, columns, diagonals
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != 0:
                return self.board[i][0]
            if self.board[0][i] == self.board[1][i] == self.board[2][i] != 0:
                return self.board[0][i]
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != 0:
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != 0:
            return self.board[0][2]
        if all(self.board[y][x] != 0 for y in range(3) for x in range(3)):
            return 0  # Draw
        return None

@commands.hybrid_command(name="ttt", description="Play Tic Tac Toe with another user")
@app_commands.describe(opponent="The user you want to challenge")
async def ttt(ctx, opponent: discord.Member):
    if opponent.bot:
        return await ctx.send("You can't play against a bot.")

    if opponent == ctx.author:
        return await ctx.send("You can't play against yourself.")

    embed = create_embed(
        title="Tic Tac Toe",
        description=(
            f"**{ctx.author.mention} (X)** vs **{opponent.mention} (O)**\n"
            f"**{ctx.author.mention}'s turn**"
        )
    )

    view = TicTacToe(ctx.author, opponent)
    await ctx.send(embed=embed, view=view)
    
    # Note: Full reminder implementation would require background tasks
@commands.hybrid_command(name="nickn", description="Change or reset someone's nickname (if allowed by role hierarchy)")
@app_commands.describe(user="The user whose nickname you want to change or reset", nickname="The new nickname (leave empty to reset)")
async def nickn(ctx, user: discord.Member, *, nickname: str = None):
    # Check if bot can manage the user
    if user.top_role >= ctx.guild.me.top_role:
        embed = create_embed(
            f"{get_emoji('cross')} Permission Error",
            f"I can't change **{user.display_name}**'s nickname because their role is higher or equal to my role!"
        )
        return await ctx.send(embed=embed)

    try:
        old_name = user.display_name
        if nickname:  # If nickname is provided
            await user.edit(nick=nickname, reason=f"Nickname changed by {ctx.author}")
            embed = create_embed(
                f"{get_emoji('tick')} Nickname Changed",
                f"**{old_name}** is now **{nickname}**"
            )
        else:  # If no nickname provided → reset
            await user.edit(nick=None, reason=f"Nickname reset by {ctx.author}")
            embed = create_embed(
                f"{get_emoji('tick')} Nickname Reset",
                f"**{old_name}**'s nickname has been reset to default username."
            )

        await ctx.send(embed=embed)

    except discord.Forbidden:
        embed = create_embed(
            f"{get_emoji('cross')} Forbidden",
            "I don't have permission to manage nicknames!"
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = create_embed(
            f"{get_emoji('cross')} Error",
            f"An error occurred: {str(e)}"
        )
        await ctx.send(embed=embed)

async def setup(bot):
    """Add fun commands to bot"""
    bot.add_command(ship)
    bot.add_command(coinflip)
    bot.add_command(dice)
    bot.add_command(eightball)
    bot.add_command(joke)
    bot.add_command(fact)
    bot.add_command(poll)
    bot.add_command(remind)
    bot.add_command(ttt)
    bot.add_command(nickn)
