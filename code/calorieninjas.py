"""
CalorieNinjas API
- RapidAPI Doc: https://rapidapi.com/blog/calorieninjas-api-with-python-php-ruby-javascript-examples/
- Official Doc: https://calorieninjas.com/api
"""

import http.client
import json
import re
import urllib.parse
from collections import defaultdict, OrderedDict

import numpy as np
import pandas as pd

query_pre = '/v1/nutrition?query='
headers = {'x-rapidapi-key': "ce19d0164fmsh3d383efc0e85ce5p16dcb1jsnb1a4a3c79541",
           'x-rapidapi-host': "calorieninjas.p.rapidapi.com"}


def open_connection():
    conn = http.client.HTTPSConnection("calorieninjas.p.rapidapi.com")
    return conn


def extract_tag(query_string, remove_metrics=True):
    regex_tag, tag_found, clean_query = r'\[(.+?)\]', 'NO_TAG', query_string
    m = re.search(regex_tag, query_string)
    if m:
        tag_found = m.group(1).upper()
        clean_query = re.sub(regex_tag, '', query_string)
    # Now take in mind below
    # clean_query = re.sub(r'[^A-Za-z\s]+', '', clean_query)
    return tag_found, clean_query.strip()


def query_for_food(connection, query):
    tag, clean_query = extract_tag(query)
    query_encoded = urllib.parse.quote(clean_query)
    full_query = f'{query_pre}{query_encoded}'

    try:
        connection.request("GET", full_query, headers=headers)
        res = connection.getresponse()
        data = res.read()
        # print(data.decode("utf-8"))
        result = json.loads(data.decode("utf-8"))['items']
    except:
        print(f'Error with {query} (clean: |{clean_query}|)')
        result = {}
    return tag, clean_query, result


def query_for_foods(connection, queries):
    return [(clean_query,
             {'title_tag': tag, 'nutrition_data': {r['name']: {i: r[i] for i in r if i != 'name'} for r in result}})
            for tag, clean_query, result in [query_for_food(connection, query) for query in queries]]


def aggregate_nutrition_component_food(nutrition_result, nutrition_keys=(
        'calories', 'carbohydrates_total_g', 'cholesterol_mg', 'fat_saturated_g',
        'fat_total_g', 'fiber_g', 'potassium_mg', 'protein_g', 'sodium_mg', 'sugar_g')):
    food_nutrition = {key: {} for key in nutrition_keys}
    for n_key in nutrition_keys:
        nutrition_coll = []
        for ingredient, nutrition in nutrition_result.items():
            # unit to 100 g
            nutrition_coll.append(np.round((nutrition[n_key] / nutrition['serving_size_g']) * 100, 2))
            # Debug
            # if nutrition['serving_size_g'] > 100:
            #    print(ingredient, nutrition['serving_size_g'], nutrition[n_key],
            #          np.round((nutrition[n_key] / nutrition['serving_size_g']) * 100, 2))
        food_nutrition[n_key]['mean'] = np.mean(nutrition_coll) if len(nutrition_coll) > 0 else None
        food_nutrition[n_key]['max'] = np.max(nutrition_coll) if len(nutrition_coll) > 0 else None
        food_nutrition[n_key]['std'] = np.std(nutrition_coll) if len(nutrition_coll) > 1 else 0 if len(
            nutrition_coll) > 0 else None

    return food_nutrition


def aggregate_nutrition_component_food_dict(nutrition_results, nutrition_keys=(
        'calories', 'carbohydrates_total_g', 'cholesterol_mg', 'fat_saturated_g',
        'fat_total_g', 'fiber_g', 'potassium_mg', 'protein_g', 'sodium_mg', 'sugar_g')):
    return [(recipe, aggregate_nutrition_component_food(r_data['nutrition_data'], nutrition_keys)) for
            recipe, r_data in nutrition_results]


def nutrition_dict_to_df(foods_list, val='mean', nutrition_keys=(
        'calories', 'carbohydrates_total_g', 'cholesterol_mg', 'fat_saturated_g',
        'fat_total_g', 'fiber_g', 'potassium_mg', 'protein_g', 'sodium_mg', 'sugar_g')):
    if val == 'mean':
        data = []
        for title, nutrition in foods_list:
            food_data = [title]
            for key in nutrition_keys:
                food_data.append(nutrition[key]['mean'])
            data.append(food_data)
        return pd.DataFrame(data, columns=['food_title'] + list(nutrition_keys))
    else:
        # todo implement other strategies, for example from De Chuhoury:
        """
            First, if the standard deviation of calorific content over all matching descriptors was less than the mean, 
            we used the mean as the aggregate calorie. Otherwise, we considered the maximum calorific content in the 
            descriptors as the aggregate for the post.
        """
        return None
