isbn = '9780375420528'
isbn_hyphenated = '978-0-37-542052-8'

# 2713 ✓
# [✓] validate
# [✓] val_13
# [✓] val_10
# [ ] convert 10 -> 13

class LengthError(Exception):
    pass

class ValidationError(Exception):
    pass

def validate (isbn:str) -> bool :
    ''' Checks if the check digit is correct, returns T/F accordingly '''
    
    # Remove hyphens https://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string
    isbn.translate(str.maketrans('', '', '-'))

    if len(isbn) == 13 :
        return val_13(isbn)
    elif len(isbn) == 10 :
        return val_10(isbn.lower())
    else:
        raise LengthError("Input isn't 10 or 13 numbers long")


def val_13 (isbn:str) :
    try:
        digits = [int(d) for d in isbn]
        # list comprehension = [x for y in z if a]
    except ValueError as err:
        raise ValidationError(f"Input contains non-integer: {err}")
    except:
        raise
        
    return ( sum(digits[0:13:2]) + sum(digits[1:13:2]) *3 ) %10 == 0


def val_10 (isbn:str) :
    try:
        # Handle x in check digit
        check = 10 if isbn[-1] == 'x' else int(isbn[-1])
        # add check back to digits
        digits = [int(d) for d in isbn[0:-1]]
        digits.append(check)
    except ValueError as err:
        raise ValidationError(f"Input contains non-integer: {err}")
        
    return ( sum( [ value*coefficient for coefficient, value in enumerate(digits, 1) ] ) ) %11 == 0


# def convert () 

