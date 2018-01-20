import os
import csv
import itertools
from pprint import pprint
import re
from shutil import copyfile


def blank_list(input_list):
    return not any(input_list)

def csv_path_to_player_list(csv_path):
    with open(csv_path, 'r') as csv_file:
        list_list = list(list(rec) for rec in csv.reader(csv_file))
    any_names_found = False
    full_list = []
    for name_list in list_list:
        if any_names_found and blank_list(name_list):
            break
        if not any_names_found and not blank_list(name_list):
            any_names_found = True
        full_list += name_list
    full_list = [n for n in full_list if n and 'Team ' not in n]
    return full_list

    #print list(itertools.chain.from_iterable(a))

def clean_all_csv():
    csv_paths = get_csvs_in_input()
    print(csv_paths)


def get_cypher():
    cypher_path = './input/2017-2-fall/SCVL - Information & League Status - Fall 2017 Registration.csv'



def get_csvs_in_input():
    dir_path = './input/2017-2-fall/'
    csv_paths = [dir_path + f for f in os.listdir(dir_path)]
    players = sum(map())
    return csv_paths


class Name(object):
    def __init__(self, name):
        first_name_re = re.compile('^(\S+) ')
        last_name_re = re.compile('^\S+ (.*)$')
        self.full = name
        self.first = re.findall(first_name_re, name)[0]
        self.last = re.findall(last_name_re, name)[0]
        self.last_name_chars = 1
        self.set_unique_name()

    def set_unique_name(self):
        self.unique = '{} {}'.format(self.first, self.last[:self.last_name_chars])

    def increment_name_length(self):
        self.last_name_chars += 1
        self.set_unique_name()

    def find_unique_names(self, b):
        while self.unique == b.unique:
            self.increment_name_length()
            b.increment_name_length()
        return self, b

    def __repr__(self):
        return '{} {} {}'.format(self.unique, self.last_name_chars, self.full)


def get_name_cypher(name_objects):
    unique_names = {}
    for name_obj in name_objects:
        if name_obj.unique in unique_names:
            if name_obj.full != unique_names[name_obj.unique].full:
                existing = unique_names.pop(name_obj.unique)
                existing, name_obj = existing.find_unique_names(name_obj)
                unique_names[existing.unique] = existing
                unique_names[name_obj.unique] = name_obj
            else:
                pass  # its already in there
        else:
            unique_names[name_obj.unique] = name_obj
    name_cypher = {name.full: name.unique for _, name in unique_names.items()}
    return name_cypher


def remake_csv(name_cypher, input_path, output_path):
    copyfile(input_path, output_path)
    with open(output_path, 'r+') as out_file:
        string = out_file.read()
    for name, unique in name_cypher.items():
        string = string.replace(name, unique)
    with open(output_path, 'r+') as out_file:
        out_file.write(string)
    print(string)


def convert_csv_path_to_new_csv(csv_path, output_path):
    with open(csv_path, 'r') as csv_file:
        list_list = list(list(rec) for rec in csv.reader(csv_file))
    player_name_list = itertools.chain.from_iterable(list_list)
    player_name_list = filter(lambda x: ' ' in x, player_name_list)
    name_objects = list(map(Name, player_name_list))
    name_cypher = get_name_cypher(name_objects)
    remake_csv(name_cypher, csv_path, output_path)


if __name__ == '__main__':
    test_path = './input/2018-1-spring/int and rec teams - Sheet1.csv'
    output_path = test_path.replace('.csv', '_clean.csv')
    convert_csv_path_to_new_csv(test_path, output_path)
