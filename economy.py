import discord
import random
from discord.ext import commands, tasks
from discord.commands import SlashCommandGroup
from Database.my_sql import mycursor as cursor
# Initialize the bot and database connection
from Database.my_sql import mydb as db
from Util.converter import comma as co
from Util.BLcheck import is_blacklisted
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from Classes.Eco_Leaderboard import EcoLead
from PIL import Image
import imageio
import os
import numpy as np
import asyncio

from datetime import datetime
import time
import datetime
class Stock:
    def __init__(self, symbol, price):
        self.symbol = symbol
        self.price = price


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stock_prices = self.fetch_stock_prices()
        self.last_stock_prices = dict(self.stock_prices)
        self.embed_message = None

        global c_success
        global c_fail
        global c_norm
        c_success = 0x93C54B
        c_fail = 0xA30000
        c_norm = 0x222222
        self.market_activity.start()  # Start the market activity task

    def fetch_stock_prices(self):
        stock_prices = {}
        cursor = db.cursor()
        cursor.execute("SELECT symbol, price FROM stocks")
        for symbol, price in cursor.fetchall():
            stock_prices[symbol] = price
        cursor.close()
        return stock_prices
    economy = SlashCommandGroup("economy", "Economy Commands")
    stocks = economy.create_subgroup("stock", "Stock commands")

    @tasks.loop(minutes=10)  # Run the task every 5 minutes
    async def market_activity(self):
        # Simulate market activity (buying and selling of stocks)
        # Update stock prices based on market activity
        cursor.execute("SELECT symbol, price FROM stocks")
        stocks_data = cursor.fetchall()
        for symbol, price in stocks_data:
            # Simulate price change between -2% and +2%
            price_change = random.uniform(-0.005, 0.005)
            new_price = float(price) * (1 + price_change)
            print(symbol, price ,new_price)
            # Update stock price and price history
            cursor.execute("UPDATE stocks SET price = %s, price_history = CONCAT_WS(',', price_history, %s) WHERE symbol = %s", (new_price, new_price, symbol))
            # Update timestamp history
            cursor.execute("UPDATE stocks SET timestamp_history = CONCAT_WS(',', timestamp_history, %s) WHERE symbol = %s", (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), symbol))
        db.commit()
        if self.embed_message:
            await self.update_embed()
    async def update_embed(self):
        embed = discord.Embed(title="Stock Market Prices", color=0x3498db)

        for symbol, current_price in self.stock_prices.items():
            last_price = self.last_stock_prices[symbol]
            percentage_change = ((current_price - last_price) / last_price) * 100

            change_indicator = "+" if percentage_change >= 0 else "-"
            
            embed.add_field(
                name=symbol,
                value=f"Price: {current_price:.2f} ({change_indicator}{abs(percentage_change):.2f}%)",
                inline=False
            )

        await self.embed_message.edit(embed=embed)
        self.last_stock_prices = dict(self.stock_prices)

    @commands.command(name="start_embed", description="Starts the dynamic stock price embed")
    @commands.is_owner()
    async def start_embed(self, ctx):
        embed = discord.Embed(title="Stock Market Prices", color=0x3498db)

        for symbol, current_price in self.stock_prices.items():
            embed.add_field(name=symbol, value=f"Price: {current_price:.2f}", inline=False)

        self.embed_message = await ctx.send(embed=embed)

    @commands.command(name="stop_embed", description="Stops the dynamic stock price embed")
    @commands.is_owner()
    async def stop_embed(self, ctx):
        if self.embed_message:
            await self.embed_message.delete()
            self.embed_message = None

    @economy.command(name="balance", description="returns your current balance")
    async def balance(self, ctx):
        authorID = ctx.author.id
        if is_blacklisted(authorID) == True:
            e = discord.Embed(title = "Forbidden", description = "You have been blacklisted by the Bot Owner. For more Information, Dm <@!792839933387472918>", color=0xff0000)
            await ctx.respond(embed=e)   


        elif is_blacklisted(authorID) == False:
            user_id = ctx.author.id
            print(user_id)
            username = str(ctx.author)
            
            cursor.execute('SELECT * FROM economy WHERE user_id = %s', (user_id,))
            user_data = cursor.fetchone()
            print(user_data)
            if user_data:
                user_cash = user_data[2]
                user_bank = user_data[3]
                user_multiplier = user_data[6]


                embed = discord.Embed(description=f'Cash: **{(user_cash)}** <:Markschein:1138922860203753603>\nBank: **{(user_bank)}** <:Markschein:1138922860203753603>\nMultiplier: {user_multiplier}', color = c_norm)
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
                await ctx.respond(embed=embed)
            else:
                # If user doesn't exist in the database, create a new entry
                cursor.execute('INSERT INTO economy (user_id, username, cash, bank,  multiplier, job, times_worked) VALUES (%s, %s,0, 100, 1.0, "None", 0)', (user_id, username))
                db.commit()
                user_balance = 100
                user_multiplier = 1.0
                user_owns = "Nothing"
                await ctx.respond("HI")
                
  
            

    @economy.command(name="withdraw", description = 'withdraw bank money to cash money, requires an amount or "all"')
    async def withdraw(self, ctx, amount):
        
        user_id = ctx.author.id
        authorID = user_id
        if is_blacklisted(authorID) == True:
            e = discord.Embed(title = "Forbidden", description = "You have been blacklisted by the Bot Owner. For more Information, Dm <@!792839933387472918>", color=0xff0000)
            await ctx.respond(embed=e)   


        elif is_blacklisted(authorID) == False:
        
            # Check if user has sufficient bank balance
            cursor.execute('SELECT cash, bank FROM economy WHERE user_id = %s', (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                cash_balance = user_data[0]
                bank_balance = user_data[1]
                if amount.lower() == "all":
                    amount = bank_balance
                else:
                    amount = int(amount)
                if amount > bank_balance:
                    await ctx.respond("Insufficient bank balance.")
                    return
                
                new_cash_balance = cash_balance + amount
                new_bank_balance = bank_balance - amount
                total = new_bank_balance + new_cash_balance
                cursor.execute('UPDATE economy SET cash = %s, bank = %s WHERE user_id = %s', (new_cash_balance, new_bank_balance, user_id))
                db.commit()
                
                embed = discord.Embed(description=f'Withdrew **{co(amount)}** <:Markschein:1138922860203753603> from your bank\nCash: **{co(new_cash_balance)}** <:Markschein:1138922860203753603>\nBank: **{co(new_bank_balance)}** <:Markschein:1138922860203753603>\nTotal: **{co(total)}** <:Markschein:1138922860203753603>', color = c_success)
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
                await ctx.respond(embed=embed)
            else:
                await ctx.respond("User not found in the database.")

    @economy.command(name="deposit", description='deposit cash money to bank money, requires an amount or "all"')
    async def deposit(self, ctx, amount):
        authorID = ctx.author.id
        if is_blacklisted(authorID) == True:
            e = discord.Embed(title = "Forbidden", description = "You have been blacklisted by the Bot Owner. For more Information, Dm <@!792839933387472918>", color=0xff0000)
            await ctx.respond(embed=e)   


        elif is_blacklisted(authorID) == False:
            user_id = ctx.author.id
            
            # Check if user has sufficient cash balance
            cursor.execute('SELECT cash, bank FROM economy WHERE user_id = %s', (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                cash_balance = user_data[0]
                bank_balance = user_data[1]
                

                if amount.lower() == "all":
                    amount = cash_balance
                else:
                    amount = int(amount)
                    if amount > cash_balance:
                        await ctx.respond("Insufficient cash balance.")
                        return
                
                new_cash_balance = cash_balance - amount
                new_bank_balance = bank_balance + amount
                total = new_bank_balance + new_cash_balance

                cursor.execute('UPDATE economy SET cash = %s, bank = %s WHERE user_id = %s', (new_cash_balance, new_bank_balance, user_id))
                db.commit()
                
                embed = discord.Embed(description=f'Deposited **{co(amount)}** <:Markschein:1138922860203753603> to your bank\nCash: **{co(new_cash_balance)}** <:Markschein:1138922860203753603>\nBank: **{co(new_bank_balance)}** <:Markschein:1138922860203753603>\nTotal: {co(total)} <:Markschein:1138922860203753603>', color = c_success)
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
                await ctx.respond(embed=embed)
            else:
                await ctx.respond("User not found in the database.")

    @economy.command(name="work", description="work to feed your family (or your greed)")
    @commands.cooldown(2, 300, commands.BucketType.user)
    async def work(self, ctx):
        authorID = ctx.author.id
        if is_blacklisted(authorID) == True:
            e = discord.Embed(title = "Forbidden", description = "You have been blacklisted by the Bot Owner. For more Information, Dm <@!792839933387472918>", color=0xff0000)
            await ctx.respond(embed=e)   


        elif is_blacklisted(authorID) == False:
            cursor.execute("SELECT cash, bank, job, times_worked FROM economy WHERE user_id = %s", (ctx.author.id,))
            result = cursor.fetchone()

            if not result:
                await ctx.respond("You need to get a job first! Use `/economy searchjob` to see all the available jobs!")
                return

            current_balance, current_bank, current_job, times_worked = result

            # Fetch job data to determine payment range
            cursor.execute("SELECT min_payment, max_payment FROM jobs WHERE job_name = %s", (current_job,))
            job_result = cursor.fetchone()

            if job_result:
                min_payment, max_payment = job_result
                
            else:
                await ctx.respond("Invalid job data")
                return

            # Calculate the amount of money earned after tax
            earnings = random.randint(min_payment, max_payment)
            tax = int(earnings * 0.07)
            net_earnings = earnings - tax

            # Update the user's balance and times_worked in the database
            new_balance = current_balance + net_earnings
            new_times_worked = times_worked + 1

            cursor.execute("UPDATE economy SET cash = %s, times_worked = %s WHERE user_id = %s", (new_balance, new_times_worked, ctx.author.id))
            db.commit()
            total = current_bank + new_balance
            embed = discord.Embed(description=f'You earned **{co(earnings)}** <:Markschein:1138922860203753603> from your work as a {current_job}! After a __7% tax__, you received **{co(net_earnings)}** <:Markschein:1138922860203753603>.\nYour balance is now **{co(total)}** <:Markschein:1138922860203753603>', color = c_success)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
            await ctx.respond(embed=embed)


    @work.error
    async def work_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            cooldown_seconds = 300
            cooldown_time = datetime.timedelta(seconds=cooldown_seconds)

            # Convert the timedelta to seconds
            cooldown_seconds = cooldown_time.total_seconds()

            # Calculate the UNIX timestamp by subtracting the cooldown seconds from the current time
            unix_timestamp = int(time.time()) + int(cooldown_seconds)

            # Format the cooldown time using time.strftime() with the UNIX timestamp
            cooldown_formatted = time.strftime("<t:%s:R>", time.gmtime(unix_timestamp))
            response = await ctx.respond(f"This command is on cooldown. You can use it {cooldown_formatted} again.")

        # Calculate the delay for deleting the response message
            delay_seconds = cooldown_seconds - 60  # Delete the message 1 minute before the cooldown expires

            # Schedule the deletion of the response message
            await asyncio.sleep(delay_seconds)
            await response.delete()

    @economy.command(name="searchjob", description="get a list of available jobs")
    async def searchjob(self, ctx):
        authorID = ctx.author.id
        if is_blacklisted(authorID) == True:
            e = discord.Embed(title = "Forbidden", description = "You have been blacklisted by the Bot Owner. For more Information, Dm <@!792839933387472918>", color=0xff0000)
            await ctx.respond(embed=e)   


        elif is_blacklisted(authorID) == False:
            user_id = ctx.author.id

            # Fetch user's times worked from the database (replace this with your database query)
            cursor.execute("SELECT times_worked FROM economy WHERE user_id = %s", (user_id,))
            user_times_worked = cursor.fetchone()[0] if cursor.rowcount > 0 else 0

            embed = discord.Embed(title="Available Jobs", color=c_norm)
              # Check if the user already exists in the database, and create an entry if not
            cursor.execute("SELECT user_id FROM economy WHERE user_id = %s", (user_id,))
            if not cursor.fetchone():
                username = ctx.author.name
                cursor.execute("INSERT INTO economy (user_id, username, cash, bank, job) VALUES (%s, %s, 0, 100, NULL)", (user_id, username))
                db.commit()

            # Fetch available job information from the 'jobs' table
            cursor.execute("SELECT job_name, min_payment, max_payment, times_worked_requirement FROM jobs")
            job_rows = cursor.fetchall()

            items_per_page = 25
            pages = [job_rows[i:i + items_per_page] for i in range(0, len(job_rows), items_per_page)]

            for job_page in pages:
                embed.clear_fields()
                for job in job_page:
                    job_name = job[0]
                    min_payment = job[1]
                    max_payment = job[2]
    
                    times_worked_requirement = job[3]
                    job_status = "Available" if times_worked_requirement <= user_times_worked else "Not Available"
                    job_name = f"{'<:locked:1138946745712250930>' if job_status == 'Not Available' else ''}{job_name}"
                    embed.add_field(name=job_name, value=f"Salary Range: {min_payment} - {max_payment} | Times Worked Requirement: {times_worked_requirement}", inline=False)

                embed.set_footer(text="- You have to work more to be able to get that job", icon_url="https://cdn.discordapp.com/emojis/1138946745712250930.webp?size=128!quality=lossless")
                await ctx.respond(embed=embed)


    @economy.command(name="getjob", description="get a job to earn some money")
    async def getjob(self, ctx, *, job_name: str):
        authorID = ctx.author.id
        if is_blacklisted(authorID) == True:
            e = discord.Embed(title = "Forbidden", description = "You have been blacklisted by the Bot Owner. For more Information, Dm <@!792839933387472918>", color=0xff0000)
            await ctx.respond(embed=e)   


        elif is_blacklisted(authorID) == False:
            user_id = ctx.author.id

            # Fetch user's times worked from the database (replace this with your database query)
            cursor.execute("SELECT times_worked FROM economy WHERE user_id = %s", (user_id,))
            user_times_worked = cursor.fetchone()[0] if cursor.rowcount > 0 else 0

            # Fetch available job information from the 'jobs' table
            cursor.execute("SELECT job_name, min_payment, max_payment, times_worked_requirement FROM jobs WHERE times_worked_requirement <= %s", (user_times_worked,))
            available_jobs = cursor.fetchall()

            selected_job = None
            for job in available_jobs:
                if job[0].lower() == job_name.lower():
                    selected_job = job
                    break

            if selected_job:
                job_name = selected_job[0]
                min_payment = selected_job[1]
                max_payment = selected_job[2]

                # Update the user's job in the database (replace this with your database update query)
                cursor.execute("UPDATE economy SET job = %s WHERE user_id = %s", (job_name, user_id))
                db.commit()

                await ctx.respond(f"{ctx.author.mention}, you've successfully obtained the job: {job_name}! Your salary range is: {co(min_payment)} - {co(max_payment)}.")
            else:
                await ctx.respond("That job is not available or doesn't exist.")



    @economy.command(name="addmoney", description="add some money to a users balance")
    @commands.is_owner()
    async def addmoney(self, ctx, member: discord.Member, amount: int):
        
        # Update the user's balance in the database (replace this with your database update query)
        cursor.execute("UPDATE economy SET bank = bank + %s WHERE user_id = %s", (amount, member.id))
        db.commit()
        e = discord.Embed(description=f"Added {co(amount)} <:Markschein:1138922860203753603> to {member.mention}'s account.", color=c_success)
        e.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)

        await ctx.respond(embed=e)

    @economy.command(name="rob", description="be criminal and rob someones money")
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def rob(self, ctx, member: discord.Member):
        authorID = ctx.author.id
        if is_blacklisted(authorID) == True:
            e = discord.Embed(title = "Forbidden", description = "You have been blacklisted by the Bot Owner. For more Information, Dm <@!792839933387472918>", color=0xff0000)
            await ctx.respond(embed=e)   


        elif is_blacklisted(authorID) == False:
            user_id = ctx.author.id
            target_id = member.id

            # Fetch user's cash and bank balances from the database (replace this with your database query)
            cursor.execute("SELECT cash, bank FROM economy WHERE user_id = %s", (user_id,))
            user_result = cursor.fetchone()
            user_cash = user_result[0] if user_result else 0
            user_bank = user_result[1] if user_result else 0

            # Fetch target's cash and bank balances from the database (replace this with your database query)
            cursor.execute("SELECT cash, bank FROM economy WHERE user_id = %s", (target_id,))
            target_result = cursor.fetchone()
            target_cash = target_result[0] if target_result else 0
            target_bank = target_result[1] if target_result else 0


            if target_cash <= 0:
                e = discord.Embed(description=f"{member.mention} doesn't have any cash to rob. Try again later.", color=c_fail)
                e.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
                await ctx.respond(embed=e)
                return
            success_rate = 0.6  # 60% success rate
            if random.random() < success_rate:
                stolen_amount = min(target_cash, random.randint(1, user_cash+1))
                user_new_cash = user_cash + stolen_amount
                target_new_cash = target_cash - stolen_amount

                # Update balances in the database (replace this with your database update queries)
                cursor.execute("UPDATE economy SET cash = %s WHERE user_id = %s", (user_new_cash, user_id))
                cursor.execute("UPDATE economy SET cash = %s WHERE user_id = %s", (target_new_cash, target_id))
                db.commit()

                e = discord.Embed(description=f"{ctx.author.mention} successfully robbed {member.mention} and stole {co(stolen_amount)} <:Markschein:1138922860203753603> cash!", color=c_success)
                e.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
                await ctx.respond(embed=e)

            else:
                # Calculate the penalty
                penalty = (user_cash + user_bank) / (target_cash + user_cash + user_bank)
                penalty_amount = int(penalty * user_cash)

                # Update balances for the caught user
                user_new_cash = max(0, user_cash - penalty_amount)
                user_new_bank = max(0, user_bank - penalty_amount)
                cursor.execute("UPDATE economy SET cash = %s, bank = %s WHERE user_id = %s", (user_new_cash, user_new_bank, user_id))
                db.commit()

                e = discord.Embed(description=f"{ctx.author.mention} attempted to rob {member.mention} but got caught! Paid {co(penalty_amount)} <:Markschein:1138922860203753603> cash as a penalty.", color=c_fail)
                e.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
                await ctx.respond(embed=e)

    @rob.error
    async def rob_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            cooldown_seconds = 1800
            cooldown_time = datetime.timedelta(seconds=cooldown_seconds)

            # Convert the timedelta to seconds
            cooldown_seconds = cooldown_time.total_seconds()

            # Calculate the UNIX timestamp by subtracting the cooldown seconds from the current time
            unix_timestamp = int(time.time()) + int(cooldown_seconds)

            # Format the cooldown time using time.strftime() with the UNIX timestamp
            cooldown_formatted = time.strftime("<t:%s:R>", time.gmtime(unix_timestamp))
            response = await ctx.respond(f"This command is on cooldown. You can use it {cooldown_formatted} again.")

        # Calculate the delay for deleting the response message
            delay_seconds = cooldown_seconds - 60  # Delete the message 1 minute before the cooldown expires

            # Schedule the deletion of the response message
            await asyncio.sleep(delay_seconds)
            await response.delete()

    @economy.command(name="crime", description="rob a bank or something")
    @commands.cooldown(2, 300, commands.BucketType.user)
    async def crime(self, ctx):
        authorID = ctx.author.id
        if is_blacklisted(authorID) == True:
            e = discord.Embed(title = "Forbidden", description = "You have been blacklisted by the Bot Owner. For more Information, Dm <@!792839933387472918>", color=0xff0000)
            await ctx.respond(embed=e)   


        elif is_blacklisted(authorID) == False:
            user_id = ctx.author.id

            # Fetch user's cash and bank balances from the database (replace this with your database query)
            cursor.execute("SELECT cash, bank FROM economy WHERE user_id = %s", (user_id,))
            user_result = cursor.fetchone()
            user_cash = user_result[0] if user_result else 0
            user_bank = user_result[1] if user_result else 0

            success_rate = 0.8  # 80% success rate
            if random.random() < success_rate:
                earned_amount = random.randint(2000, 100000)
                user_new_cash = user_cash + earned_amount

                # Update balance in the database (replace this with your database update query)
                cursor.execute("UPDATE economy SET cash = %s WHERE user_id = %s", (user_new_cash, user_id))
                db.commit()
                e = discord.Embed(description=f"{ctx.author.mention} successfully committed a crime and earned {earned_amount} <:Markschein:1138922860203753603> cash!", color=c_success)
                e.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
                await ctx.respond(embed=e)
            else:
                fine = min(user_cash, random.randint(2000, 100000))
                user_new_cash = user_cash - fine

                # Update balance in the database (replace this with your database update query)
                cursor.execute("UPDATE economy SET cash = %s WHERE user_id = %s", (user_new_cash, user_id))
                db.commit()
                e = discord.Embed(description=f"{ctx.author.mention} attempted a crime but got caught and paid a fine of {fine} <:Markschein:1138922860203753603> cash.", color=c_fail)
                e.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
                await ctx.respond(embed=e)


    @crime.error
    async def crime_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            cooldown_seconds = 300

            cooldown_time = datetime.timedelta(seconds=cooldown_seconds)

            # Convert the timedelta to seconds
            cooldown_seconds = cooldown_time.total_seconds()

            # Calculate the UNIX timestamp by subtracting the cooldown seconds from the current time
            unix_timestamp = int(time.time()) + int(cooldown_seconds)

            # Format the cooldown time using time.strftime() with the UNIX timestamp
            cooldown_formatted = time.strftime("<t:%s:R>", time.gmtime(unix_timestamp))
            response = await ctx.respond(f"This command is on cooldown. You can use it {cooldown_formatted} again.")

        # Calculate the delay for deleting the response message
            delay_seconds = int(cooldown_seconds) - 60  # Delete the message 1 minute before the cooldown expires

            # Schedule the deletion of the response message
            await asyncio.sleep(delay_seconds)
            await response.delete()

    @economy.command(name="quitjob", description="quit your job")
    async def quitjob(self, ctx):
        authorID = ctx.author.id
        if is_blacklisted(authorID) == True:
            e = discord.Embed(title = "Forbidden", description = "You have been blacklisted by the Bot Owner. For more Information, Dm <@!792839933387472918>", color=0xff0000)
            await ctx.respond(embed=e)   


        elif is_blacklisted(authorID) == False:
            user_id = ctx.author.id

            # Fetch user's job from the database (replace this with your database query)
            cursor.execute("SELECT job FROM economy WHERE user_id = %s", (user_id,))
            user_result = cursor.fetchone()
            user_job = user_result[0] if user_result else None

            if user_job is None:
                await ctx.respond("You don't have a job to quit.")
                return

            # Update job to None in the database (replace this with your database update query)
            cursor.execute("UPDATE economy SET job = NULL WHERE user_id = %s", (user_id,))
            db.commit()

            e = discord.Embed(description=f"{ctx.author.mention} has quit their job as {user_job}.", color=c_success)
            e.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
            await ctx.respond(embed=e)



#Stocks
############################################ 







    def update_stock_prices(self):
        cursor.execute("SELECT symbol, price FROM stocks")
        stocks_data = cursor.fetchall()

        for stock_data in stocks_data:
            symbol, price = stock_data
            fluctuation = random.uniform(-0.05, 0.05)  # Simulate a fluctuation between -5% and +5%
            new_price = float(price) * (1 + fluctuation)
            
            cursor.execute("UPDATE stocks SET price = %s WHERE symbol = %s", (new_price, symbol))
            db.commit()
           

    @stocks.command()
    async def quote(self, ctx):
        authorID = ctx.author.id
        if is_blacklisted(authorID) == True:
            e = discord.Embed(title = "Forbidden", description = "You have been blacklisted by the Bot Owner. For more Information, Dm <@!792839933387472918>", color=0xff0000)
            await ctx.respond(embed=e)   


        elif is_blacklisted(authorID) == False:
            cursor.execute("SELECT symbol, price FROM stocks")
            stock_data = cursor.fetchall()

            if stock_data:
                quotes = [f"{symbol}: ${price:.2f}" for symbol, price in stock_data]
                quotes_message = "\n".join(quotes)

                embed = discord.Embed(description="Stocks", color=c_norm)
                embed.add_field(name=quotes_message, value = "")
                embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)

                await ctx.respond(embed=embed)
            else:
                await ctx.respond("No stocks found.")


    @stocks.command(name="buy", description="buy a stock!")
    async def buy(self, ctx, symbol, quantity):
        authorID = ctx.author.id
        if is_blacklisted(authorID) == True:
            e = discord.Embed(title="Forbidden", description="You have been blacklisted by the Bot Owner. For more Information, Dm <@!792839933387472918>", color=0xff0000)
            await ctx.respond(embed=e)
        elif is_blacklisted(authorID) == False:
            cursor.execute("SELECT symbol, price FROM stocks WHERE symbol = %s", (symbol,))
            stock_data = cursor.fetchone()
            if stock_data:
                stock = Stock(stock_data[0], stock_data[1])
                total_price = stock.price * int(quantity)
                user_id = ctx.author.id

                cursor.execute("SELECT bank, IMAW, IMBG, IMGR, IMPJ, MACB, MAY FROM economy WHERE user_id = %s", (user_id,))
                user_data = cursor.fetchone()

                if user_data and user_data[0] >= total_price:
                    bank_balance, imaw_quantity, imbg_quantity, imgr_quantity, impj_quantity, macb_quantity, may_quantity = user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_data[5], user_data[6]

                    if symbol == "IMAW":
                        imaw_quantity += int(quantity)
                    elif symbol == "IMBG":
                        imbg_quantity += int(quantity)
                    elif symbol == "IMGR":
                        imgr_quantity += int(quantity)
                    elif symbol == "IMPJ":
                        impj_quantity += int(quantity)
                    elif symbol == "MACB":
                        macb_quantity += int(quantity)
                    elif symbol == "MAY":
                        may_quantity += int(quantity)
                    else:
                        await ctx.respond("Invalid stock symbol.")
                        return

                    new_bank_balance = bank_balance - total_price

                    cursor.execute("UPDATE economy SET bank = %s, IMAW = %s, IMBG = %s, IMGR = %s, IMPJ = %s, MACB = %s, MAY = %s WHERE user_id = %s", (new_bank_balance, imaw_quantity, imbg_quantity, imgr_quantity, impj_quantity, macb_quantity, may_quantity, user_id))
                    cursor.execute("INSERT INTO transactions (user_id, symbol, quantity, price) VALUES (%s, %s, %s, %s)", (user_id, symbol, int(quantity), stock.price))

                    price_increase = random.uniform(0.005, 0.02)  # Price increase between 0.5% and 2%
                    new_price = float(stock.price) * (1 + price_increase)
                    cursor.execute("UPDATE stocks SET price = %s WHERE symbol = %s", (new_price, symbol))
                    # Update price history and timestamp
                    cursor.execute("UPDATE stocks SET price_history = CONCAT_WS(',', price_history, %s), timestamp_history = CONCAT_WS(',', timestamp_history, %s) WHERE symbol = %s", (new_price, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), symbol))

                    db.commit()

                    embed = discord.Embed(description=f"Successfully bought {quantity} {symbol} shares for ${total_price:.2f}", color=c_success)
                    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
                    await ctx.respond(embed=embed)

                else:
                    await ctx.respond("Insufficient balance.")
            else:
                await ctx.respond("Stock not found.")


    @stocks.command(name="sell", description="sell your stocks")
    async def sell(self, ctx, symbol, quantity):
        authorID = ctx.author.id
        if is_blacklisted(authorID) == True:
            e = discord.Embed(title="Forbidden", description="You have been blacklisted by the Bot Owner. For more Information, Dm <@!792839933387472918>", color=0xff0000)
            await ctx.respond(embed=e)
        elif is_blacklisted(authorID) == False:
            cursor.execute("SELECT symbol, price FROM stocks WHERE symbol = %s", (symbol,))
            stock_data = cursor.fetchone()
            if stock_data:
                stock = Stock(stock_data[0], stock_data[1])
                user_id = ctx.author.id

                cursor.execute("SELECT bank, IMAW, IMBG, IMGR, IMPJ, MACB, MAY FROM economy WHERE user_id = %s", (user_id,))
                user_data = cursor.fetchone()

                if user_data:
                    bank_balance, imaw_quantity, imbg_quantity, imgr_quantity, impj_quantity, macb_quantity, may_quantity = user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_data[5], user_data[6]

                    if symbol == "IMAW":
                        stock_quantity = imaw_quantity
                    elif symbol == "IMBG":
                        stock_quantity = imbg_quantity
                    elif symbol == "IMGR":
                        stock_quantity = imgr_quantity
                    elif symbol == "IMPJ":
                        stock_quantity = impj_quantity
                    elif symbol == "MACB":
                        stock_quantity = macb_quantity
                    elif symbol == "MAY":
                        stock_quantity = may_quantity
                    else:
                        await ctx.respond("Invalid stock symbol.")
                        return

                    if stock_quantity >= int(quantity):
                        new_bank_balance = bank_balance + stock.price * int(quantity)

                        if symbol == "IMAW":
                            imaw_quantity -= int(quantity)
                        elif symbol == "IMBG":
                            imbg_quantity -= int(quantity)
                        elif symbol == "IMGR":
                            imgr_quantity -= int(quantity)
                        elif symbol == "IMPJ":
                            impj_quantity -= int(quantity)
                        elif symbol == "MACB":
                            macb_quantity -= int(quantity)
                        elif symbol == "MAY":
                            may_quantity -= int(quantity)

                        cursor.execute("UPDATE economy SET bank = %s, IMAW = %s, IMBG = %s, IMGR = %s, IMPJ = %s, MACB = %s, MAY = %s WHERE user_id = %s", (new_bank_balance, imaw_quantity, imbg_quantity, imgr_quantity, impj_quantity, macb_quantity, may_quantity, user_id))
                        cursor.execute("INSERT INTO transactions (user_id, symbol, quantity, price) VALUES (%s, %s, %s, %s)", (user_id, symbol, -int(quantity), stock.price))

                        price_decrease = random.uniform(0.005, 0.02)  # Price decrease between 0.5% and 2%
                        new_price = float(stock.price) * (1 - price_decrease)

                        cursor.execute("UPDATE stocks SET price = %s WHERE symbol = %s", (new_price, symbol))
                        # Update price history and timestamp
                        cursor.execute("UPDATE stocks SET price_history = CONCAT_WS(',', price_history, %s), timestamp_history = CONCAT_WS(',', timestamp_history, %s) WHERE symbol = %s", (stock.price, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), symbol))

                        db.commit()

                        embed = discord.Embed(description=f"Successfully sold {quantity} {symbol} shares for ${stock.price * int(quantity):.2f}", color=c_success)
                        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
                        await ctx.respond(embed=embed)

                    else:
                        await ctx.respond("You don't own enough of that stock.")
                else:
                    await ctx.respond("User not found in the database.")
            else:
                await ctx.respond("Stock not found.")





    @stocks.command(name="showstocks", description="shows your stocks")
    async def show_stocks(self, ctx):
        authorID = ctx.author.id
        if is_blacklisted(authorID) == True:
            e = discord.Embed(title="Forbidden", description="You have been blacklisted by the Bot Owner. For more Information, Dm <@!792839933387472918>", color=0xff0000)
            await ctx.respond(embed=e)
        elif is_blacklisted(authorID) == False:
            user_id = ctx.author.id
            cursor.execute("SELECT * FROM economy WHERE user_id = %s", (user_id,))
            user_data = cursor.fetchone()

            if user_data:
                owned_stocks = []
                stock_columns = ["IMAW", "IMBG", "IMGR", "MACB", "MAY"]
                
                for col in stock_columns:
                    if user_data[cursor.column_names.index(col)] > 0:
                        owned_stocks.append((col, user_data[cursor.column_names.index(col)]))

                if owned_stocks:
                    embed = discord.Embed(description=" ", color=c_norm)
                    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)

                    for stock_symbol, quantity in owned_stocks:
                        embed.add_field(name=f"Owned {stock_symbol}:", value=f"{quantity} shares", inline=False)

                    await ctx.respond(embed=embed)
                else:
                    await ctx.respond("You don't own any stocks.")
            else:
                await ctx.respond("User not found in the database.")







      

    # ... (other imports and code)  

    @stocks.command(name="graph", description="Generate and display a stock price history graph")
    async def graph(self, interaction: discord.Interaction, symbol):
        # ... (other code)

        authorID = interaction.user.id
        if is_blacklisted(authorID) == True:
            e = discord.Embed(title="Forbidden", description="You have been blacklisted by the Bot Owner. For more Information, Dm <@!792839933387472918>", color=0xff0000)
        elif is_blacklisted(authorID) == False:
            cursor.execute("SELECT price_history, timestamp_history FROM stocks WHERE symbol = %s", (symbol,))
            stock_data = cursor.fetchone()
            message = await interaction.response.defer()

            if stock_data:
                price_history = stock_data[0].split(',')
                timestamp_history = stock_data[1].split(',')

                # Filter out empty strings or non-numeric values from price_history
                price_history = [float(price) for price in price_history if price.strip() and price.replace(".", "", 1).isdigit()]
                timestamp_history = [datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S.%f') for ts in timestamp_history]

                fig, ax = plt.subplots()
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
                plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=3))  # Adjust the interval as needed
                plt.gca().yaxis.set_major_locator(plt.MultipleLocator(10))  # Set y-axis to show in steps of 10

                # Prepare the animation
                ani_frames = []
                for i in range(len(timestamp_history)):
                    ax.clear()
                    plt.plot(timestamp_history[:i], price_history[:i])
                    plt.axvline(x=timestamp_history[i], color='gray', linestyle='--', linewidth=0.5)
                    plt.gcf().autofmt_xdate()
                    plt.title(f"{symbol} Stock Price History")
                    plt.xlabel("Time")
                    plt.ylabel("Price")

                    # Convert plot to image
                    plt.draw()
                    img = np.array(plt.gcf().canvas.renderer.buffer_rgba())

                    ani_frames.append(img)

                # Create and save the animated video
                video_path = "stock_graph.mp4"
                imageio.mimsave(video_path, ani_frames, fps=6)
                await interaction.followup.send(file=discord.File(video_path))
                plt.close()
            else:
                await interaction.response.send_message("Stock not found.")

    @economy.command(name="leaderboard")
    async def stock_leaderboard(self, ctx):
        await ctx.respond(" ", view=EcoLead(), ephemeral=True)


# Schedule stock price updates every minute




def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Economy(bot)) # add the cog to the bot