import json
class ISBNError(Exception):
    pass

library_data:dict = {}

with open('db.json', 'r') as db:
    # Read and deserialize db into memory
    library_data:dict = json.loads(db.read())

def add (book:dict):
    # Check if an ISBN already exists
    if search(book["isbn"]):
        # If so, bounce
        raise ISBNError("ISBN already exists")
    else:
        # Else add book
        append_data({book["isbn"]: book})

def search (isbn):
    # Search db for ISBN key
    return isbn in library_data["books"]

def append_data (new_data:dict):
    # Add new book data to memory-db
    library_data["books"].update(new_data)
    
    # Write memory to file
    with open("db.json", 'w') as db:
        json.dump(library_data, db, indent=4)

def complete (isbn, id):
    # Update library_data in memory
    library_data["books"][isbn]['completions'].append(id)

    # Write memory to file
    with open("db.json", 'w') as db:
        json.dump(library_data, db, indent=4)

def rate (isbn, id, rating):
    # Update library_data in memory
    library_data["books"][isbn]['ratings'].update({str(id): int(rating)})

    # Write memory to file
    with open("db.json", 'w') as db:
        json.dump(library_data, db, indent=4)