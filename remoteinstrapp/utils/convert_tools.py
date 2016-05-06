"""
This module allows to manipulate transformations to hexadecimal string forms and viceversa. It is widely used for the
manager that wraps PyVisa objects.
"""
__author__ = 'macastro'


import re


def simple_hex_to_formal_hex(hex_simple_str):
    """
     String transformations,from hex string to formal format Example: str = 'AA2F510003' will be '\xAA\x2F\x51\x00\x03'
     returning an empty str if not possible
    :param hex_simple_str: simple hex format
    :return: str: log hex format \\x
    """
    pat = re.compile(r'([0-9A-Fa-f])+')  # checking of hexadecimal notation
    if not pat.match(hex_simple_str) and len(hex_simple_str) % 2 != 0:  # if it is odd ... returns ""
        return ''
    hex_str = ''
    i = 0
    while i < len(hex_simple_str): # we build the formal hexadecimal string
        hex_str += r'\x' + hex_simple_str[i:i + 2]
        i += 2

    return hex_str


def to_byte(hex_simple_str):
    '''
    From string to byte. Notice that this must have hexadecimal values.
    :param hex_simple_str: string with hexadecimal values
    :return: python byte object
    '''
    return bytes.fromhex(hex_simple_str)


def to_str(byte_obj):
    '''
    Try to convert a byte object with the format b' \0xMN\0xPQ...' to a string to hex format as following type 'MNPQ...'
    where the length of it, is an even number.
    :param byte_obj: python byte object
    :return: string with hexadecimal values
    '''
    str_decodes = byte_obj.decode('latin-1') # we use latin-1 because it gives us more capacity
    # for greater hexadecimal numbers
    hex_str = ''
    for ch in str_decodes:
        hex_str += hex(ord(ch))

    # Now we build the final string using between a list that has been filled with 0 in case of a
    # digit after 0X comes alone. For instance 0x1 would be 0x01 and 0xa3 would remain 0xa3

    return ''.join(['0' + el if len(el) == 1 else el for el in hex_str.split('0x')][1:])

