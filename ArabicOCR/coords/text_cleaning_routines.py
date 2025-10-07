import json
from bidi.algorithm import get_display
import re

def correct_brackets(text):
    text = switch_chars(text, '{', '}')
    text = switch_chars(text, '(', ')')
    text = switch_chars(text, '[', ']')
    text = switch_chars(text, '«', '»')
    return text

def switch_chars(text, x, y):
    t = list(text)
    ind_x = [i for i,j in enumerate(t) if j==x]
    ind_y = [i for i,j in enumerate(t) if j==y]
    for i in ind_x:
        t[i] = y
    for i in ind_y:
        t[i] = x
    return ''.join(t)

def clean_text(input_text):
    cleaned_text = input_text.replace('\u0009', ' ')
    cleaned_text = cleaned_text.replace('\u000A', ' ')
    cleaned_text = cleaned_text.replace('\u00D7', 'x')
    cleaned_text = cleaned_text.replace('\u066A', '%')    
    cleaned_text = cleaned_text.replace('\u06f3', '\u0663')
    cleaned_text = cleaned_text.replace('\u06f7', '\u0667')
    cleaned_text = cleaned_text.replace('\u06f9', '\u0669')
    
    
    cleaned_text = cleaned_text.replace('\u2018', "'")
    cleaned_text = cleaned_text.replace('\u2019', "'")
    cleaned_text = cleaned_text.replace('\u201C', '"')
    cleaned_text = cleaned_text.replace('\u201D', '"')
    cleaned_text = cleaned_text.replace('…', '...')    
    cleaned_text = cleaned_text.replace('\u2033', "\u064b")
    cleaned_text = cleaned_text.replace('\u2044', '/')
    cleaned_text = cleaned_text.replace('\u2e17', '\u201e')
    pattern = r'[\u2013\u2014]'
    cleaned_text = re.sub(pattern, '-', cleaned_text)
    pattern = r'[●•\xb7]'
    cleaned_text = re.sub(pattern, '.', cleaned_text)
    return cleaned_text
    
    
def get_char_sets():
    english_lower = range(ord('a'), ord('z')+1)
    english_upper = range(ord('A'), ord('Z')+1)
    
    english_numbers = range(ord('0'), ord('9')+1)

    english_ord = set(english_lower).union(english_upper)
    english_numbers = {chr(c) for c in set(english_numbers)}
    english_alphabet = {chr(c) for c in english_ord}

    # This includes numerals/digits also
    arabic_unicodes = range(ord("\u0600"), ord("\u06ff")+1)
    arabic_ord = set(arabic_unicodes)
    arabic_chars = {chr(c) for c in arabic_ord}
    arabic_numbers_ord = range(ord("\u0660"), ord("\u0669")+1)
    arabic_digits = {chr(c) for c in arabic_numbers_ord}
    return {'english_alphabet': english_alphabet, 'arabic_unicodes': arabic_chars, 
            'latin_digits': english_numbers, 'arabic_digits': arabic_digits}    


def get_clean_visual_order(text):
    charset_dict = get_char_sets()
    text_set = set(text)
    has_english_alphabet = len(text_set.intersection(charset_dict['english_alphabet'])) > 0
    has_latin_digits = len(text_set.intersection(charset_dict['latin_digits'])) > 0
    has_arabic_digits = len(text_set.intersection(charset_dict['arabic_digits'])) > 0
    


    if has_arabic_digits or has_english_alphabet or has_latin_digits:
        text_visual_order = get_display(text, base_dir='R')[::-1]
        text_visual_order = correct_brackets(text_visual_order)
    else:
        text_visual_order = text
    clean_visual_order = clean_text(text_visual_order)
    return clean_visual_order
