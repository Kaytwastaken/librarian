# system
from random import choice
from dotenv import dotenv_values
from datetime import datetime
from statistics import mean
# discord.py
import discord
from discord.ext import commands
# homebrew
from isbn import LengthError, ValidationError, validate
import db
from docs import help_embed
books = db.library_data["books"]

config = dotenv_values('.env')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=config["PREFIX"], intents=intents, activity=discord.Activity(name='the Village Library', type=discord.ActivityType.watching), help_command=None )  # type: ignore

startTime = datetime.now()

async def send_unhandled_error(ctx, err):
    error_embed = discord.Embed(
        color=discord.Color.dark_red(),
        title='Unhandled error!',
        description=f'{config["UNHANDLED_ERROR"]}'
    )
    error_embed.add_field(name='Error', value=err)

    await ctx.send(embed=error_embed)
    raise err

async def send_named_error(ctx, err, message=''):
    error_embed = discord.Embed(
        color=discord.Color.red(),
        title=err,
    )
    if message != '':
        error_embed.add_field(name='Error', value=message)

    await ctx.send(embed=error_embed)

async def validate_book_id(id):
    try:
        int(id)
    except ValueError:
        for isbn in books:
            if books[isbn]['title'] == id:
                return isbn
    else:
        try:
            validate(id)
        except LengthError as err:
            raise err
        except ValidationError as err:
            raise err
        except Exception as err:
            raise err
        
        if validate(id):
            print(id)
            return id
        else:
            raise ValueError("Invalid ISBN")
                

async def validate_book_r8(rating):
    if rating != '':
        try:
            int(rating)
        except ValueError:
            raise ValueError("That rating doesn't look right! A rating can only be a whole number from 1 to 10.")
        else:
            if int(rating) > 10 or int(rating) < 1:
                raise ValueError("A rating can only be a whole number from 1 to 10.")

@bot.event
async def on_ready():
    print(f'Bot authenticated as {bot.user}!')

@bot.command(brief='View bot and command help!', usage='help isbn')
async def help(ctx, name=''):
    
    '''
    View general bot help or detailed information on each command.
    '''
    
    await ctx.send(embed=help_embed(bot, name))

@bot.command(brief='Add a book to the library!', usage='add "Girls can kiss now : essays" "Jill Gutowitz" 9781982158507 "nonfiction,essays,queer"')
async def add(ctx, title: str = '', author:str = '', isbn: str = '', tags: str = ''):
    
    '''
    Adds a book to the library with a "Title", "Author", ISBN, and, optionally, "comma,separated,tags".
    '''

    temp_book = {'title': '', 'author': '', 'isbn': '', 'tags': [], 'ratings': {}, 'completions': []}

    if title == '':
        await send_named_error(ctx,'''What's the name of the book?''', '`Missing argument: title`')
        return
    if author == '':
        await send_named_error(ctx, "Who's the author?", '`Missing argument: author`')
        return
    if isbn == '':
        await send_named_error(ctx, "What's the ISBN?", '`Missing argument: ISBN`')
        return
    if tags != '':
        temp_book['tags'] = [tag.strip() for tag in tags.split(',')]
    
    temp_book['title'] = title
    temp_book['author'] = author
    
    try:
        validate(isbn)
    except ValueError as err:
        await send_named_error(ctx, "That ISBN doesn't look quite right!", f'`Invalid ISBN: {err}`')
        return
    except Exception as err:
        await send_unhandled_error(ctx, err)
        return
    else:
        if not validate(isbn):
            await send_named_error(ctx, "Invalid ISBN!")
            return
    
    temp_book['isbn'] = isbn
    
    working_message = await ctx.send(
        embed=discord.Embed(
            color=discord.Color.yellow(),
            title=f'Adding "{temp_book["title"]}"'
        )
    )
    try:
        db.add(temp_book)
    except db.ISBNError:
        await send_named_error(ctx, 'A book with that ISBN already exists!')
        await working_message.delete(delay=1)
    except Exception as err:
        print('error in exceotion throw')
        await send_unhandled_error(ctx, err)
    else:
        success_embed = discord.Embed(
            color=discord.Color.green(),
            title=f'Successfully added "{temp_book["title"]}" to the library'
        )
        success_embed.add_field(name='Title', value=temp_book["title"])
        success_embed.add_field(name='Author', value=temp_book["author"])
        success_embed.add_field(name='Tags', value=', '.join(str(tag) for tag in temp_book["tags"]) if temp_book["tags"] != [] else "N/A")

        await ctx.send(embed=success_embed)
        await working_message.delete(delay=1)

@bot.command(aliases=['data'], brief="View an overview of the Library's data!", usage='stats')
async def stats(ctx):
    
    """
    Shows an overview of all the library's data.
    Currently displays total number of books, favorite book (based on average rating), and most popular book (based on number of completions).
    """

    # Bounce if the library is empty
    if books == {}:
        await send_named_error(ctx, "The library is empty!")
        return

    def complete_sort(isbn):
        return len(books[isbn]["completions"])
    complete_sorted = sorted(books, key=complete_sort, reverse=True)

    def favorite_sort(isbn):
        if books[isbn]['ratings'] == {}:
            return 0
        return mean(books[isbn]['ratings'].values())
    favorite_sorted = sorted(books, key=favorite_sort, reverse=True)

    stats_embed = discord.Embed(
        color=discord.Color.purple(),
        title='Current library statistics!'
    )
    # Total entries, number of entries in top 5 tags, most popular book (based on number of completions), and favorite book (based on average rating)
    stats_embed.add_field(name='Total books', value=len(books))
    stats_embed.add_field(name='Most popular book', value=f""" "{books[complete_sorted[0]]['title']}" with {len(books[complete_sorted[0]]['completions'])} completions""", inline=False)
    stats_embed.add_field(name='Favorite book', value=f""" "{books[favorite_sorted[0]]['title']}" with a rating of {mean(books[favorite_sorted[0]]['ratings'].values())}/10""", inline=False)
    # avg_rating = 
    # [ ] When there are actually enough tags add the top 5 to stats
    # [ ] When a book is added add its tags to known_tags
    # stats_embed.add_field(inline=False, name='Top 5 tags', value='tag:#\ntag:#\ntag:#\ntag:#\ntag:#')
    
    await ctx.send(embed=stats_embed)

@bot.command(aliases=['done', 'complete'], brief='Complete a book and give it a rating!', usage='finish 9781982158507 10')
async def finish(ctx, id='', rating=''):
    
    """
    Mark a book as complete and optionally give it a rating.
    You can only mark a book as complete once, but can update your rating at any time with `lib!rate`
    """
    
    if id == '':
        await send_named_error(ctx, 'What book is it?', '`Missing argument: title / ISBN`')
        return
    
    book_isbn = ''
    
    # Validate book id
    try:
        book_isbn = await validate_book_id(id)
    except ValueError as err:
        await send_named_error(ctx, "That ID doesn't look quite right! Is the title or ISBN exact?")
        return
    except ValidationError as err:
        await send_named_error(ctx, "That ISBN doesn't look quite right!", f'`Invalid ISBN: {err}`')
        return
    except LengthError as err:
        await send_named_error(ctx, "That ISBN doesn't look quite right!", f'`Invalid ISBN: {err}`')
        return

    # Validate rating
    try:
        await validate_book_r8(rating)
    except ValueError as err:
        await send_named_error(ctx, err)
        return

    if ctx.message.author.id in books[book_isbn]['completions']:
        await ctx.send(embed=discord.Embed(
            color=discord.Color.yellow(),
            title="You've already finished this book! Use `lib!rate` to update your rating."
        ))
        return
    
    # Update completions in db
    db.complete(book_isbn, ctx.message.author.id)
    completion_embed = discord.Embed(
        color=discord.Color.green(),
        title=f"""Congrats on finishing "{books[book_isbn]['title']}"!"""
    )
    completion_embed.add_field(name='Current Completions', value=len(books[book_isbn]['completions']))
    
    if rating != '':
        # Update rating in db
        db.rate(book_isbn, ctx.message.author.id, int(rating))
        avg_rating = mean(books[book_isbn]['ratings'].values())
        completion_embed.add_field(name='New Rating', value=avg_rating)

    await ctx.send(embed=completion_embed)

@bot.command(brief='Update your rating of a book!', usage='rate 9781982158507 10')
async def rate(ctx, id='', rating=''):
    
    """
    Update or add a rating to any book you've marked as complete.
    """
    
    if id == '':
        await send_named_error(ctx, 'What book is it?', '`Missing argument: title / ISBN`')
        return
    
    if rating == '':
        await send_named_error(ctx, "What's your rating'?", '`Missing argument: rating`')
        return

    book_isbn = ''
    
    # Validate book id
    try:
        book_isbn = await validate_book_id(id)
    except ValueError as err:
        await send_named_error(ctx, "That ID doesn't look quite right! Is the title or ISBN exact?", f"{err}")
        return
    except ValidationError as err:
        await send_named_error(ctx, "That ISBN doesn't look quite right!", f'`Invalid ISBN: {err}`')
        return
    except LengthError as err:
        await send_named_error(ctx, "That ISBN doesn't look quite right!", f'`Invalid ISBN: {err}`')
        return
    
    # Validate rating
    try:
        await validate_book_r8(rating)
    except ValueError as err:
        await send_named_error(ctx, err)
        return

    if ctx.message.author.id not in books[book_isbn]['completions']:
        await ctx.send(embed=discord.Embed(
            color=discord.Color.yellow(),
            title="You haven't completed this book yet, use `lib!finish` to mark a book as complete."
        ))
        return

    # Update rating in db
    db.rate(book_isbn, ctx.message.author.id, int(rating))

    avg_rating = mean(books[book_isbn]['ratings'].values())
    
    rate_embed = discord.Embed(
        color=discord.Color.green(),
        title=f"""Updating your rating on "{books[book_isbn]['title']}"!"""
    )
    rate_embed.add_field(name='New Rating', value=avg_rating)

    await ctx.send(embed=rate_embed)

@bot.command(brief="Add new tags to a book!", usage='tag 9781982158507 "heartwrenching at times, but still nonfiction"')
async def tag(ctx, isbn, tags:str = ''):
    
    '''
    Add new tags to a book after it's been added to the library! Skips over existing tags and preserves the order tags are added in.
    '''

    try:
        validate(isbn)
    except ValueError as err:
        await send_named_error(ctx, "That ISBN doesn't look quite right!", f'`Invalid ISBN: {err}`')
        return
    except LengthError as err:
        await send_named_error(ctx, "That ISBN doesn't look quite right!", f'`Invalid ISBN: {err}`')
        return
    except Exception as err:
        await send_unhandled_error(ctx, err)
        return
    else:
        if validate(isbn):
            # If book doesnt exist bounce
            if isbn not in books.keys():
                await send_named_error(ctx, "That book couldn't be found!", f"No book with isbn: `{isbn}` found. Is it the correct ISBN?")
                return
        else:
            await send_named_error(ctx, "Invalid ISBN!")
            return

    book = books[isbn]
    new_tags = [tag.strip() for tag in tags.split(',')]
    book["tags"] = book["tags"] + [tag for tag in new_tags if tag not in book["tags"]]

    try:
        db.append_data({book["isbn"]: book})
        # {book["isbn"]: book}
    except Exception as err:
        await send_unhandled_error(ctx, err)

    book_embed = discord.Embed(
        color=discord.Color.green(),
        title=f"""Successfully updated "{book['title']}" !"""
    )

    book_embed.add_field(name="New Tags", value=', '.join(str(tag) for tag in book["tags"]) if book["tags"] != [] else "N/A", inline=False)
    
    await ctx.send(embed=book_embed)

    return


@bot.command(name='random', aliases=['rec', 'recme'], brief='Picks a random book for you to read!', usage='random "scifi,fantasy" strict')
async def random_book( ctx, tags:str = '', method:str = 'loose'):
    
    '''
    Picks a random book from the library with the specified tags.
    Loose tag matching returns all books with any of the specified tags, strict matching returns only books with all the specified tags.
    Defaults to loose matching.
    '''

    random_isbn:str  = ''
    random_book:dict = {}
    
    if tags != '':
        user_tags = tags.split(',')
        valid_books:list = []
        
        book_objs = books.values()

        def loose(book):
            return len(set(user_tags).intersection(book["tags"])) != 0
        
        def strict(book):
            return set(user_tags).issubset(book["tags"])

        tag_algorithms = {
            "loose": loose,
            "strict": strict
        }
        
        # Loose tag matching - returns all books with any specifed tags
        valid_books = [book for book in book_objs if tag_algorithms[method](book)]
        # valid_books = all books for every book in books that returns true on loose matching
        
        if valid_books == []:
            await send_named_error(ctx, 'No books with those tags were found! Maybe try loose matching (`lib!rec "tags" loose`) or fewer tags.')
            return
        
        random_book = choice(valid_books)
        random_isbn = random_book["isbn"]
        
    else:
        random_isbn = choice(list(books.keys()))
        random_book = books[random_isbn]
    

    rec_embed = discord.Embed(
        color=discord.Color.from_str('#ff6161'),
        title=f""" "{random_book['title']}" """
    )

    rec_embed.add_field(name="Author", value=random_book["author"], inline=True)
    rec_embed.add_field(name="Rating", value='10/10', inline=True)
    rec_embed.add_field(name="Completions", value=len(random_book["completions"]), inline=True)
    rec_embed.add_field(name="Tags", value=', '.join(str(tag) for tag in random_book["tags"]) if random_book["tags"] != [] else "N/A", inline=False)
    rec_embed.add_field(name="WorldCat", value=f"https://worldcat.org/search?q={random_isbn}", inline=False)
    rec_embed.add_field(name="B&N", value=f"https://www.barnesandnoble.com/s/{random_isbn}", inline=False)
    
    await ctx.send(embed=rec_embed)

@bot.command(aliases=['book'], brief="Stats on a specific book", usage='view 9781982158507')
async def view (ctx, isbn):
    '''
    View information on a specific book!
    '''
    
    try:
        validate(isbn)
    except ValueError as err:
        await send_named_error(ctx, "That ISBN doesn't look quite right!", f'`Invalid ISBN: {err}`')
        return
    except LengthError as err:
        await send_named_error(ctx, "That ISBN doesn't look quite right!", f'`Invalid ISBN: {err}`')
        return
    except Exception as err:
        await send_unhandled_error(ctx, err)
        return
    else:
        if validate(isbn):
            # If book doesnt exist bounce
            if isbn not in books.keys():
                await send_named_error(ctx, "That book couldn't be found!", f"No book with isbn: `{isbn}` found. Is it the correct ISBN?")
                return
        else:
            await send_named_error(ctx, "Invalid ISBN!")
            return
    
    # If checks passed do the thing
    book = books[isbn]

    book_embed = discord.Embed(
        color=discord.Color.purple(),
        title=f""" "{book['title']}" """
    )

    book_embed.add_field(name="Author", value=book["author"], inline=True)
    book_embed.add_field(name="Rating", value='10/10', inline=True)
    book_embed.add_field(name="Completions", value=len(book["completions"]), inline=True)
    book_embed.add_field(name="Tags", value=', '.join(str(tag) for tag in book["tags"]) if book["tags"] != [] else "N/A", inline=False)
    book_embed.add_field(name="WorldCat", value=f"https://worldcat.org/search?q={isbn}", inline=False)
    book_embed.add_field(name="B&N", value=f"https://www.barnesandnoble.com/s/{isbn}", inline=False)
    
    await ctx.send(embed=book_embed)

@bot.command(brief='Bot version and uptime', usage='meta')
async def meta (ctx):
    
    '''
    Display current bot version, uptime, etc.
    '''
    
    meta_embed = discord.Embed(
        color=discord.Color.purple(),
        title='Bot information'
    )
    meta_embed.add_field(name='Version', value='v0.2.0')
    meta_embed.add_field(name='Uptime', value=datetime.now() - startTime)
    meta_embed.add_field(name='Gender', value="Assigned Female By Cayman")
    meta_embed.add_field(inline=False, name='Github', value='https://github.com/Kaytwastaken/librarian')
    meta_embed.add_field(inline=False, name='Discord.py', value='https://github.com/Rapptz/discord.py')

    await ctx.send(embed=meta_embed)

@bot.command(hidden=True)
async def error(ctx):
    try:
        print(0/0)
    except Exception as err:
        await send_unhandled_error(ctx, err)

token = config['TOKEN']
bot.run(token) #type: ignore
# type ignore bc its saying it cant cast str | None to str