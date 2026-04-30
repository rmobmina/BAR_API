#!/usr/bin/python3

import cgi
import MySQLdb
import json
import urllib.request, urllib.error, urllib.parse
import math

# Retrieve parameters
arguments = cgi.FieldStorage()
species = arguments['species'].value
binSize = arguments['binSize'].value

# Print header
print('Content-Type: application/json\n')

try:
    gene = {}
    if species == 'Arabidopsis_thaliana':
        con = MySQLdb.connect('localhost', 'SAMPLE_USER', 'SAMPLE_PW', 'eplant2')
        cur = con.cursor()
        query = 'SELECT geneId,start,end FROM tair10_gff3 WHERE type=\"gene\";'
        cur.execute(query)

        # Create and initialize bins for each chromosome
        chrLengths = [30427671, 19698289, 23459830, 18585056, 26975502, 154478, 366924]
        chrNames = ['1', '2', '3', '4', '5', 'C', 'M']
        bins = [[], [], [], [], [], [], []]

        for n in range(7):
            for m in range(int(math.ceil(float(chrLengths[n]) / float(binSize)))):
                bins[n].append(0)

        for row in cur:
            index = chrNames.index(row[0][2])
            startBin = int(math.floor(float(row[1]) / float(binSize)))
            endBin = int(math.floor(float(row[2]) / float(binSize)))
            for n in range(startBin, endBin + 1):
                bins[index][n] += 1

        chrNames = ['Chr 1', 'Chr 2', 'Chr 3', 'Chr 4', 'Chr 5', 'Chr C', 'Chr M']
        output = []
        for n in range(7):
            output.append({'name': chrNames[n], 'density': bins[n]})

        print(json.dumps(output))
except:
    print('{}')
