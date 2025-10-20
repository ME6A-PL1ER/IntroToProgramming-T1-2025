def to_camel_case(text):
    words = text.replace('-', ' ').replace('_', ' ').split()
    first = words[0].lower()
    rest = ''.join(word.capitalize() for word in words[1:])
    return first + rest