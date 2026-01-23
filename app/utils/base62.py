import string

characters = string.digits + string.ascii_letters

def encode(num):
    if num == 0:
        return characters[0]

    encoded_str = ""
    while num > 0:
        num, rem = divmod(num, len(characters))
        encoded_str += characters[int(rem)]

    return encoded_str