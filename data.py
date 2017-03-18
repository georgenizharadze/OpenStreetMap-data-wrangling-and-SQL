#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import csv
import codecs
import cerberus
from time import time
import sqlite3
from pprint import pprint
import Schema
SCHEMA = Schema.schema


"""
The following set of codes audits and cleans street designations according to the same principles as in
the P3 Case Study exercises.
"""
street_type_re = re.compile(r'\b\S+\.?$', re.UNICODE | re.IGNORECASE)

expected =['вулиця'.decode('utf-8'), 'бульвар'.decode('utf-8'), 'тупик'.decode('utf-8'), 'проїзд'.decode('utf-8'),
          'проспект'.decode('utf-8'), 'алея'.decode('utf-8'), 'шосе'.decode('utf-8'), 'набережна'.decode('utf-8'),
          'узвіз'.decode('utf-8'), 'дорога'.decode('utf-8'), 'провулок'.decode('utf-8'), 'площа'.decode('utf-8'),
          'шоссе'.decode('utf-8')]

street_mapping = { 'ул.'.decode('utf-8') : 'вулиця'.decode('utf-8'),
           'ул'.decode('utf-8') : 'вулиця'.decode('utf-8'),
           'пл.'.decode('utf-8') : 'площа'.decode('utf-8'), 
           'шоссе-2'.decode('utf-8') : 'шоссе'.decode('utf-8'),
           'улица'.decode('utf-8') : 'вулиця'.decode('utf-8')
            }


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osmfile, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    return street_types


def update_name(name, street_mapping):
    m = street_type_re.search(name)
    if m and m.group() in street_mapping:
        name = re.sub(street_type_re, street_mapping[m.group()], name)
    return name

"""
The following set of codes audits and cleans up phone numbers in the 'tags' of the 'nodes' and 'ways' 
elements. 
"""

# the four regular expressions below were designed to capture the four different broad formats in which
# the phone numbers were present in the OSM file 
regex_38 = re.compile(r'(3)\W*(8)\W*(0)\W*(\d)\W*(\d)\W*(\d)\W*(\d)\W*(\d)\W*(\d)\W*(\d)\W*(\d)\W*(\d)\b')
regex_0xx = re.compile(r'^\W?(0)\W*(\d{2})\W*(\d)\W*(\d)\W*(\d)\W*(\d)\W*(\d)\W*(\d)\W*(\d)\b')
regex_800 = re.compile(r'^(0|8)\W*(800)\W*(\d)\W*(\d)\W*(\d)\W*(\d)\W*(\d)\W*(\d)\b')
regex_xxx = re.compile(r'^(\d{3})\W*(\d{2})\W*(\d{2})$')

# to address 36 specific phone numbers which were in really bad formats and could not be captured by
# the above regexes, I manually created the correction dictionary below. It will be fed into a code later. 
phone_mapping = {
    '(44)4247431' : '+38-044-424-7431',
     '+1 347 868 0740' : '+1-347-868-0740', 
     '+3-044-257-20-97' : '+38-044-257-2097',
     '+3-8-044-446-77e-70' : '+38-044-446-7770',
     '+30 (44) 536-99-06; +30 (44) 536-99-08; +30 (44) 536-99-07' : '+38-044-536-9906', 
     '+3044 401-42-94' : '+38-044-401-4294',
     '+30442556013' : '+38-044-255-6013', 
     '+38 44 2784864' : '+38-044-278-4864', 
     '+38 44 425 03 98' : '+38-044-4250-0398', 
     '+380 (044) 235-73-82' : '+38-044-235-7382', 
     '+380 (044) 275-33-00' : '+38-044-275-3300', 
     '+380 (044) 360 02 09' : '+38-044-360 0209', 
     '+380 (044) 486-18-08' : '+38-044-486-1808', 
     '+380 (067) 912-20-66' : '+38 067 912-2066', 
     '+380 44 01010' : 'ERRONEUS', 
     '+380 9905577327' : '+38-099-055-77327', 
     '+380(044) 528-30-47' : '+38-044-528-3047',
     '+380-044-4172526' : '+38-044-417-2526', 
     '+3800675055958' : '+38-067-505-5958', 
     '+3804118875' : 'ERRONEOUS', 
     '+38986073213' : '+38-098-607-3213',
     '+39 044 5939575' : '+38-044-593-9575',
     '+800 1800 1800' : 'ERRONEUOUS', 
     '044526' : 'ERRONEOUS', 
     '08005005000' : 'ERRONEOUS', 
     '102' : ' ERRONEOUS', 
     '234-55-83;234-05-88;235-23-21' : '+38-044-234-5583', 
     '287-32-11 066-563-57-29' : '38-044-287-3211', 
     '2870711,2870020' : '+38-044-287-0711', 
     '2876149,2876216' : '+38-044-287-6149', 
     '4-60-85' : 'ERRONEOUS', 
     '5-74-41' : 'ERRONEOUS',
     '67 401 21 66, 044 287 5252' : '+38-067-401-2166', 
     '8097-331-17-93' : '+38-097-331-1793', 
     '88003000500' : 'ERRONEOUS', 
 u'\u0420\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0442\u0443\u0440\u0430 - (044) 408-03-41, \u0412\u044b\u0437\u043e\u0432 \u0432\u0440\u0430\u0447\u0430 - (044) 408-74-40, \u041d\u0435\u043e\u0442\u043b\u043e\u0436\u043d\u0430\u044f \u043f\u043e\u043c\u043e\u0449\u044c - (044) 497-60-61'
: '38-044-408-0341'}

# the function below standardizes phone numbers - in vast majority of cases by string extraction and reconstruction 
# and in the remaining cases - by the use of the correction dictionary
def standardize_phone(number, phone_mapping):
    stnd = ''
    if regex_38.search(number):
        m = regex_38.search(number)
        stnd = stnd + '+' + m.group(1) + m.group(2) + '-' + m.group(3) + m.group(4) + m.group(5) + '-' + m.group(6) + \
                m.group(7) + m.group(8) + '-' + m.group(9) + m.group(10) + m.group(11) + m.group(12)
    elif regex_800.search(number):
        m = regex_800.search(number)
        stnd = stnd + m.group(1) + '-' + m.group(2) + '-' + m.group(3) + m.group(4) + m.group(5) + '-' + m.group(6) + \
                m.group(7) + m.group(8)
    elif regex_0xx.search(number):
        m = regex_0xx.search(number)
        stnd = stnd + '+38-' + m.group(1) + m.group(2) + '-' + m.group(3) + m.group(4) + m.group(5) + '-' + m.group(6) + \
                m.group(7) + m.group(8) + m.group(9) 
    elif regex_xxx.search(number):
        m = regex_xxx.search(number)
        stnd = stnd + '+38-044-' + m.group(1) + '-' + m.group(2) + '-' + m.group(3)
    else:
        stnd = phone_mapping[number]
    return stnd
	

"""
The section below incorporates the above data cleaning functions in the 'shape_element'
function and puts the data into csv files, in the same way as in the case study. 
"""

OSM_PATH = "kyiv_sample.osm"
NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'((\w|_)+):((\w|_)+:?.*)')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':
        for i in node_attr_fields:
            if i in element.attrib.keys():
                node_attribs[i] = element.attrib[i]
            else:
                # creating a placeholder ID and user name for the one missing uid / user name entry 
                node_attribs[i] = 111111
        for j in element.iter('tag'):
            prob = PROBLEMCHARS.search(j.attrib['k'])
            colon = LOWER_COLON.search(j.attrib['k'])
            if prob:
                pass
            elif colon:
                d = {'id':element.attrib['id']}
                d['key'] = colon.group(3)
                d['type'] = colon.group(1)
                if j.attrib['k'] == 'addr:street':
                    # fixing street name with previously designed function  
                    d['value'] = update_name(j.attrib['v'], street_mapping)
                elif j.attrib['k'] == 'contact:phone':
                    # standardizing phone number with previously designed function 
                    d['value'] = standardize_phone(j.attrib['v'], phone_mapping)
                else: 
                    d['value'] = j.attrib['v']
                tags.append(d)
            else:
                d = {'id':element.attrib['id']}
                d['key'] = j.attrib['k']
                d['type'] = default_tag_type
                if j.attrib['k'] == 'phone':
                    # standardizing phone number with previously designed function
                    d['value'] = standardize_phone(j.attrib['v'], phone_mapping)
                else:
                    d['value'] = j.attrib['v']
                tags.append(d)
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        for i in way_attr_fields:
            way_attribs[i] = element.attrib[i]
        for j in element.iter('tag'):
            prob = PROBLEMCHARS.search(j.attrib['k'])
            colon = LOWER_COLON.search(j.attrib['k'])
            if prob:
                pass
            elif colon:
                d = {'id':element.attrib['id']}
                d['key'] = colon.group(3)
                d['type'] = colon.group(1)
                if j.attrib['k'] == 'addr:street':
                    # fixing street name with previously designed function  
                    d['value'] = update_name(j.attrib['v'], street_mapping)
                elif j.attrib['k'] == 'contact:phone':
                    # standardizing phone number with previously designed function
                    d['value'] = standardize_phone(j.attrib['v'], phone_mapping)
                else: 
                    d['value'] = j.attrib['v']
                tags.append(d)
            else:
                d = {'id':element.attrib['id']}
                d['key'] = j.attrib['k']
                d['type'] = default_tag_type
                if j.attrib['k'] == 'phone':
                    # standardizing phone number with previously designed function
                    d['value'] = standardize_phone(j.attrib['v'], phone_mapping)
                else:
                    d['value'] = j.attrib['v']
                tags.append(d)
        counter = 0 
        for k in element.iter('nd'):
            d = {'id':element.attrib['id']}
            d['node_id'] = k.attrib['ref']
            d['position'] = counter
            way_nodes.append(d)
            counter += 1
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

# helper function 1
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

# helper function 2
def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_strings = (
            "{0}: {1}".format(k, v if isinstance(v, str) else ", ".join(v))
            for k, v in errors.iteritems()
        )
        raise cerberus.ValidationError(
            message_string.format(field, "\n".join(error_strings))
        )

# helper function 3
class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

# main function
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])

if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=False)