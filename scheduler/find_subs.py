#!/usr/local/bin/python
__author__ = 'brcoulter'
from pprint import pprint



#High Tier		Mid Tier		Low Tier   SUBJECTIVE TIERS

def get_sub_lists():
    # 8 10 12
    import csv
    import re
    file_path = '/Users/coulter/Desktop/life_notes/2016_q4/sub_for_playoffs/2017_spring_subs.tsv'
    with open(file_path, 'r') as file:
        reader = csv.reader(file, delimiter='\t')
        tier_names = ['Low Tier', 'Mid Tier', 'High Tier']
        col_for_div = [12, 10, 8]
        in_a_division = False
        total_divisions = 5
        sub_lists = [[[],[],[]] for _ in range(total_divisions)]
        current_divisions = total_divisions
        def filter_parentesis(string):
            to_remove = re.compile(' ?\(.\)')
            return re.sub(to_remove, '', string)
        for line in reader:
            if not in_a_division:
                if line[col_for_div[0]] in tier_names:
                    in_a_division = True
                    current_divisions -= 1
                    continue
            else:
                row_values = [line[col] for col in col_for_div]
                for idx, value in enumerate(row_values):
                    if value:
                        value = filter_parentesis(value)
                        sub_lists[current_divisions][idx].append(value)
                if not any(row_values):
                    in_a_division = False
    return sub_lists


def find_subs_for_day():
    div_sub_lists = get_sub_lists()
    pprint(div_sub_lists)

if __name__ == '__main__':
    find_subs_for_day()