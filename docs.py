import discord
from dotenv import dotenv_values

config = dotenv_values('.env')

custom_helps = {
    "isbn": {
        "brief": "What is, and how to find a book's ISBN",
        "help":
            """
            ISBNs, or International Standard Book Numbers, are numbers assigned to every commercially published book. There are 10 and 13 digit versions. This bot works with both, but 10-digit ISBNs are converted to their 13-digit equivalents.
            
            ISBNs are printed alongside copyright and distributor information on the cover page. If you can't find it there, go to a website like https://worldcat.org and search for the book's title. On WorldCat, the ISBN is listed under the 'show more information' dropdown.
            """
    }
}

def help_embed (bot, name) :
    if name == '':
        # Construct and return full help embed
        help_embed = discord.Embed(
            color=discord.Color.purple(),
            title='Welcome to Librarian!',
            description=
            """
            Librarian is a bot for managing book recommendations and rating them! 
            
            All of its commands are listed below! Arguments in <> are required, arguments in [] are optional; /s denote alises and different options.
            If you run into any issues please check the github, and follow what the error message says!
            """
        )
        help_embed.add_field(inline=False, name='lib!help [command / isbn]', value='Prints this message or information on and examples of a specific command.')
        help_embed.add_field(inline=False, name="""lib!add <"Book Title"> <"Author's Name> <10  / 13 digit ISBN> ["comma,separated,tags]""", value='Add a new entry to the library!')
        help_embed.add_field(inline=False, name='lib!stats', value="""Sends an overview of all the library's stats, including total entries, favorite book, and most popular book!""")
        help_embed.add_field(inline=False, name='lib!view/book <isbn>', value='View an overview of a specific book!')
        help_embed.add_field(inline=False, name='lib!finish/complete/done <ISBN / Title (title has to be exact)> [1-10]', value="""Increment a book's 'completions' counter and add your rating from 1 to 10 to the average rating!""")
        help_embed.add_field(inline=False, name='lib!rate <ISBN / Title (title has to be exact)> <1-10>', value="""Update your rating of the specified book!""")
        help_embed.add_field(inline=False, name='lib!tag <isbn>', value='Add new tags to a book!')
        # help_embed.add_field(inline=False, name='lib!hot/top [1+] [tag]', value='Lists the most popular x  books in a specific tag. Defaults to the top 10 and all tags')
        # help_embed.add_field(inline=False, name='lib!favorites [1+] [tag]', value='Lists the highest-rated x  books in a specific tag. Defaults to the top 10 and all tags')
        help_embed.add_field(inline=False, name='lib!random/rec/recme ["comma,separated,tags"] [strict/loose]', value='Picks a random book from the library with the specified tags.')
        help_embed.add_field(inline=False, name='lib!meta', value='Prints bot data.')

        help_embed.set_footer(text="developed with ❤ by kayt_was_taken")

        return help_embed

    command = bot.get_command(name)
    # If bot command
    if command != None and command in bot.commands and command.hidden == False:
        return construct_doc_embed(command)
    
    # If custom help
    elif command == None and name in custom_helps:
        return construct_doc_embed(name, False)
    
    # If unknown
    else:
        return discord.Embed(
            color=discord.Color.red(),
            title=f"""Command `{name}` not found! Use `lib!help` to see all available commands."""
        )

def construct_doc_embed (command, included = True) :
    # If custom help
    if included == False:
        # Return embed formed from custom_helps data
        help_embed = discord.Embed(
            color=discord.Color.purple(),
            title=custom_helps[command]["brief"],
            description=custom_helps[command]["help"]
        )
        help_embed.set_footer(text=f"lib!help {command}")

        return help_embed
    
    # If bot command
    help_embed = discord.Embed(
        color=discord.Color.purple(),
        title=command.brief,
        description=command.help
    )
    help_embed.add_field(name='Example', value=f'{config["PREFIX"]}{command.usage}')
    help_embed.add_field(name='Aliases', value=', '.join(str(alias) for alias in command.aliases) if command.aliases != [] else 'N/A')
    help_embed.set_footer(text=f"{config['PREFIX']}help {command.name}")

    return help_embed