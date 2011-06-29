from django import template



register = template.Library()



def letter(index):
    """
    Convert a number from 1 to 26 into a capital letter A-Z.
    """
    return chr(index + 64)



@register.filter
def letter_key(index):
    """
    Convert a number to its equivalent in a base-26 alphabetic enumeration:
    (1 = A, 2 = B, ..., 26 = Z, 27 = AA, 28 = AB, ..., 53 = BA...).

    """
    ret = ""
    while index > 0:
        mod = index % 26
        index /= 26
        if not mod:
            index -= 1
        ret = letter(mod or 26) + ret
    return ret
