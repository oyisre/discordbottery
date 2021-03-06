from discord.ext import commands
import random
import os
import markovify
import re

class Markov:
    """markov generate your friends
    you'll have to have used `log once in the last 12ish hours to `markov
    uses Markovify (https://github.com/jsvine/markovify)"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def markov(self, ctx, user="", *, seed: str=""):
        """markov sentence MAKER. will occasionally fail with no output
        `markov [user] [seed]
        `markov without a user picks a random user
        seed must be exactly 2 words
        a silent failure is likely due to an untalkative user being chosen or
        the previous `log data was deleted (so do `log again)"""
        server = ctx.message.server
        directory = 'data/' + server.name + ' - ' + server.id + '/Markov/'
        file_list = []
        for entry in os.scandir(directory):
            if entry.is_file() and not entry.name.endswith('.json'):
                file_list.append(entry.name)
        if user == "" or user.lower() == "random":
            file = file_list[random.randrange(0, stop=len(file_list))]
            user = file #file[0:-5]
            for member in server.members:
                if member.id == user:
                    user = member.name
        else:
            file = ""
            for member in server.members:
                if member.name.lower() == user.lower() or \
                        member.id == user or member.nick == user:
                    file = member.id #+ '.json'
                    user = member.name
            if file == "":
                await self.bot.say('couldnt find that user')
                return
        #file = file[0:-5]  # minus .json
        with open(directory + file, mode='r',
                  encoding='utf-8') as f:
            text = f.read()
        if seed == "":
            state_s = 2
        else:
            state_s = len(seed.split())
        #chain = markovify.Chain.from_json(text)
        #text_model = markovify.Text.from_chain(text)
        text_model = MyMarkov(text, state_size=state_s)  # make markov each time
        output = None
        attempts = 0
        if seed == "":
            while output is None and attempts < 17:
                attempts += 1
                if attempts < 11:
                    output = text_model.make_sentence(tries=4)
                else:
                    output = text_model.make_sentence(
                        max_overlap_ratio=1, max_overlap_total=15, tries=4)
        else:
            while output is None and attempts < 17:
                attempts += 1
                if attempts < 11:
                    output = text_model.make_sentence_with_start(seed, tries=4)
                else:
                    output = text_model.make_sentence_with_start(
                        seed, max_overlap_ratio=1,
                        max_overlap_total=15, tries=4)
        if output is not None:
            await self.bot.say(user + ": " + output)
        else:
            print(user + ' markovnfail')

    def _get_random_markov_file(self, server):
        """ Get a random user's log file """
        directory = 'data/' + server.name + ' - ' + server.id + '/Markov/'
        file_list = []
        for entry in os.scandir(directory):
            if entry.is_file() and entry.name.endswith('.json'):
                file_list.append(entry.name)
        file = file_list[random.randrange(0, stop=len(file_list))]
        user = file[0:-5] # remove '.json' to get user id
        for member in server.members:
            if member.id == user:
                user = member.name
        return user, file

    @commands.command(name='log', pass_context=True)
    async def _get_logs(self, ctx):
        """grabs the entire chatlog of the server. don't use it more than 
        once in a while or else.........."""
        # get current server
        server = None
        for s in self.bot.servers:
            if s == ctx.message.server:
                server = s
        # create folder for server log
        directory = 'data/' + server.name + ' - ' + server.id + '/Markov'
        if not os.path.exists(directory):
            os.mkdir(directory)
        directory += '/'
        print(directory)
        users = dict()
        for channel in server.channels:
            async for message in self.bot.logs_from(channel, limit=100000):
                if not message.content.startswith('`markov') or \
                        not message.content.startswith('`markovn'):
                    if message.author.id in users.keys():
                        users[message.author.id] += message.content + '\n'
                    else:
                        users[message.author.id] = message.content + '\n'
            for key in users.keys():
                with open(directory + key, mode='w', encoding='utf-8') as file:
                    file.write(users[key])
        print('donelogs')

    @commands.command(name='genMarkov', pass_context=True)
    async def _generate_markov(self, ctx):
        """useless function"""
        for server in self.bot.servers:
            directory = 'data/' + server.name + ' - ' + server.id + '/Markov/'
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if not file.endswith('.json'):
                        with open(directory + file, mode='r',
                                  encoding='utf-8') as f:
                            text = f.read()
                        text_model = markovify.NewlineText(text)
                        with open(directory + file + '.json', mode='w',
                                  encoding='utf-8') as f:
                            f.write(text_model.chain.to_json())
        print('donemarkovifys')

class MyMarkov(markovify.NewlineText):
    """overrides to enable emojis and dumb punctuation"""

    def word_split(self, sentence):
        """
        include unicode
        """
        word_split_pattern = re.compile('\s+', flags=re.U)
        return re.split(word_split_pattern, sentence)

    def test_sentence_input(self, sentence):
        """
        no filter hahahahahaha
        """
        return True
