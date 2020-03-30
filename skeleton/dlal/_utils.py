def snake_to_upper_camel_case(s):
    return ''.join(i.capitalize() for i in s.split('_'))
