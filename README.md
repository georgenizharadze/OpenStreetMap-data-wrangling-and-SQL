# OpenStreetMap data wrangling, SQL design and data analysis

In this project I deal with a large volume of incomplete and messy data. I desing and implement a programmatic audit and clean-up, design an relational database schema and transfer the processed data to SQL, where it can be queried and analyzed efficiently. 

## Map area

I selected Kyiv, the capital of Ukraine, for my study. I happened to work and live there for over
five years and know the city quite well. Therefore, I had a natural interest to explore this area
and relate the OpenStreetMap information to my own knowledge and experiences.
Additionally, I was curious to get a feel for the engagement of people in data crowdsourcing
and the completeness and quality of the data in an emerging country like Ukraine. Finally, I
wanted to work with some non-Latin text to get practice in handling unicode strings.
I downloaded the preselected metro area of Kyiv from [Map Zen](https://mapzen.com/data/metro-extracts/metro/kyiv_ukraine/). The full uncompressed size of the osm file was just over 300 MB. I used smaller sample files, 30
MB and 3 MB, in size, for initial auditing and schema compliance validation, respectively.

## Data overview

I parsed the full XML file and quantified a number of parameters to get an overall view of the data. 

Types and quantities of nodes:  
   `'node': 1,401,056`  
   `'nd': 1,721,147`  
   `'bounds': 1`  
   `'member': 79,530`  
   `'tag': 618,817`  
   `'relation': 7,350  `
   `'way': 212,674`  
   `'osm': 1`  

Below is a summary of string structures of the key (“k”) descriptions in the “tag” nodes. I used
the same 3 categories as in the case study exercises, namely, lowercase, lowercase with colon,
presence of problematic characters and “other”. The breakdown below is of the total number
of “k” descriptions and also on the basis of unique ones:

   |       |All “k” descriptions|Unique “k” descriptions|
   |-------|:------------------:|----------------------:|
   |lower  |463,963|480|
   |lower\_colon|154,137|540|
   |problemchars|0|0|
   |other|717|133|
   |Total|618,817|1,153|

It is noteworthy that there are no “k” descriptions at all which contain problematic characters.
Additionally, I counted unique contributors by the user id (“uid”) both in “nodes” and “way” nodes and the number came to 2,288.
I also counted unique street names and the number came to 1,646. However, some street names related to the same street were spelled in different ways. Therefore, the actual number of unique underlying streets is fewer than this.

## Problems identified

Through a programmatic audit, I identified the following problems:

*Completeness issues*
* Missing user ID and user name in a “nodes” node: one node did not have any entry for user – neither user name, nor ID. I adjusted the `shape_element` function code to include in this node a placeholder user id and user name, which I could later query and identify in SQL.
* As mentioned above, the number of unique streets in the OSM file is less than 1,646. From Wikipedia and other sources, I understood that the actual number of different streets in Kyiv is more than 1,900. This suggests that not all the streets have been mapped in OSM.

*Consistency issues*
* Through initial audit, I found the number of unique user IDs in the OSM file to be 2,288, and the number of unique user names - 2,292. This appeared inconsistent and I hypothesized that it was due to four users changing their user names while using the same user ID. After importing the data to SQL, I ran queries to check this and it indeed appeared to be the case. Four user IDs below have two user names listed for each:

    675506|MapDrawerXXX15
    
    675506|XardasNetpoint
    
    448601|stream13
    
    448601|Andrew Shelestov
    
    4147527|fly777
    
    4147527|fly\_kiev
    
    4711657|Veniamin Zolotukhin
    
    4711657|Venya Zolotukhin

* The programmatic audit of street names helped me identify a number of issues with the consistency of street name representation. Some of the problems were due to the use of different types of abbreviations, use or non-use of the dot ‘.’ character, etc. In other cases, inconsistency arose due to use of two different (but related) languages – Ukrainian and Russian, both of which are prevalent in Ukraine. For example, the word “street” would in some cases (majority of cases) be present in Ukrainian and in others – in Russian. In the clean-up, I replaced Russian end words by Ukrainian. Overall, I identified 5 types of required corrections (see below) to end words, which I included in the “mapping” dictionary, which served as an input for the “update_name” function, which I subsequently incorporated in the “shape_element” function.

    `mapping = { 'ул.'.decode('utf-8') : 'вулиця'.decode('utf-8'),
    'ул'.decode('utf-8') : 'вулиця'.decode('utf-8'),
    'пл.'.decode('utf-8') : 'площа'.decode('utf-8'),
    'шоссе-2'.decode('utf-8') : 'шоссе'.decode('utf-8'),
    'улица'.decode('utf-8') : 'вулиця'.decode('utf-8')
    }`

* I also detected that in several tags, unconventional designation was used for street address under “k”. Namely, instead of “addr:street”, either 'addr:street:en' or 'addr:street_1' was present. However, I established that this was the case in only 11 out of the total of c. 618K tags, therefore, I did not consider that this issue merited additional code modification and clean-up.

* Phone numbers were in a major disarray, presented in lots of different and sometimes hard to comprehend formats. A standard representation of landline phone numbers in Ukraine follows the format of +38-044-XXX-XXXX. Mobile numbers follow the same standard but the three-digit code after the country code (+38) varies by operator. In addition, there are some local 800 numbers, which usually follow the format 0-800-XXX-XXX. I formulated regexes and audited the OSM file. Having gotten deeper insights in the audit process, I refined the regexes and cleaned up / standardized the phone numbers. I managed to deal with the vast majority of numbers by programmatic string extraction and string reconstruction. A few remaining cases which were too non-standard, I dealt with by constructing a correction dictionary which I later fed into a code.

## Data exploration through SQL database

### Users(contributors)

Counting unique users in both “nodes” and “ways” nodes and ranking them by the number of appearance:

  `SELECT uid, user, COUNT(\*) as num from (SELECT uid, user FROM nodes UNION ALL SELECT uid, user from ways) as united GROUP BY uid ORDER     BY num DESC;`
    
`Output, top 10:
[(561414, u'Freeways\_me', 160871),
(1676637, u'Kilkenni', 120949),
(371387, u'matvey_kiev_ua', 93157),
(440812, u'dudka', 64077),
(435936, u'Legioner', 49977),
(648633, u'kulyk', 45594),
(348674, u'Cabeleira', 43623),
(188947, u'D_i_m', 35208),
(353472, u'Barbos', 34878),
(1872841, u'1gorok', 32352)]`

It is striking how many contributions each of these top users have made. I counted the total number of “ways” and “nodes” attributable to the top 50 users (out of the total of 2,288):

  `SELECT sum(num) FROM (SELECT uid, COUNT(\*) as num from (SELECT uid FROM nodes UNION ALL SELECT uid from ways) as united GROUP BY uid       ORDER BY num DESC LIMIT 50) as topsomany;`
   
The result came to 1,209,007. This is c. 75% of the total number of “ways” and “nodes”. This shows a striking pareto phenomenon – only about 2% of users being responsible for about three quarters of the information in the system.

### Amenities

I retrieved all unique types of amenities by the following query:
  `SELECT DISTINCT value FROM (SELECT value FROM nodes\_tags WHERE key == "amenity") as allamenities ORDER BY value;`
  
There are 119 different types of amenities. I browsed through them and select ones which I was curious to explore in more detail. Namely, I decided to look into arts centres, ATMs, co-working spaces and restaurants. 
Retrieving the names of arts centres:
   `SELECT id, value FROM nodes\_tags WHERE key == "name" AND id IN (SELECT id FROM nodes\_tags WHERE key == "amenity" and value ==           "arts_centre");`

`306524501|Центр пам'яткознавства
742273893|Пінчук Арт Центр
1927478283|Дитячо-підлітковий клуб «Виноградар»
2537586155|Квартира 57
2537586158|Я на Хорива
2900786556|Гапчинська
2907097705|Bottega
2907097707|A-house
2907097709|Триптих-арт
2954869432|Митець
3010080046|MEZZANINE
3087148673|Арткластер «Видубичі»
3506121766|Центр Леся Курбаса(Державний центр театральних мистецтв ім.Леся Курбаса)
3789104261|Галерея 36
3789169357|Галерея Триптих`

Querying the total number ATMs: 
  `SELECT COUNT (\*) FROM nodes\_tags WHERE key == "amenity" and value == "atm";
  Result: 741`

Querying the names of ATM operators:
  `SELECT DISTINCT value FROM nodes\_tags WHERE key == "operator" AND id IN (SELECT id FROM nodes\_tags WHERE key == "amenity" and value ==   "atm") ORDER BY value;`

A small extract of results:

`Credit Agricole
Crédit Agricole
Euronet
Euronet Worldwide
Euronet worldwide
…..
FidoBank
Fidobank
Forward Bank
…….
Marfin Bank
OTP Bank
OTPbank
…..
UniCredit Bank
UniCreditBank
Unicredit
Unicredit Bank
Universal Bank
…..
VAB
VAB Банк`

We see that there is an issue with bank names – the same bank is often spelled in several different ways. This is problematic. For example, if we want to see how many ATMs there are in the city per each operator, we cannot readily do the grouping. We would have to do additional serious pre-processing of bank names to harmonize the spelling. 

Co-working spaces are a new development in Kyiv and I was curious to see how many were listed in OSM and what their names were. The query and output are below: 

  `SELECT id, value FROM nodes\_tags WHERE key == "name" AND id IN (SELECT id FROM   nodes\_tags WHERE key == "amenity" and value ==           "coworking_space");`

`3125606725|БеседниZzа
3452527225|БеседниZza
3708816818|MediaHub
4030243416|Неробоче місце - коворкінг
4047682810|HUB 4.0`

One co-working space seems to be present in OSM twice, under different IDs. So, it appears that there are four different co-working spaces documented in OSM. 

Analyzing restaurants: 

Total number of restaurants: 
    
  `SELECT COUNT (\*) FROM nodes\_tags WHERE key == "amenity" and value == "restaurant";
  Result: 743`

Top 10 cuisines by number of restaurants:

  `SELECT value, count(\*) as num FROM nodes\_tags WHERE key == "cuisine" AND id IN (SELECT id FROM   nodes\_tags WHERE key == "amenity" and   value == "restaurant") GROUP BY value ORDER BY num DESC limit 10;`

`Result:
regional|50
italian|49
pizza|28
japanese|25
sushi|17
international|14
asian|11
georgian|11
chinese|9
burger|8`

Then I queried for all the data available on Georgian restaurants, as it is my home country. The query is below but I’m not pasting the data output here for the economy of space.

`SELECT * FROM nodes_tags WHERE id IN (SELECT id FROM nodes_tags WHERE key == "amenity" and value == "restaurant") AND  id IN (SELECT id FROM nodes_tags WHERE key == "cuisine" and value IN ("georgian", "грузинская", "грузинская_кухня"));`


### Infrastructure

In my past career I worked in the power generation and distribution business. I saw in OpenStreetMap documentation that the system contains some data on electricity infrastructure. Therefore, I decided to explore this. 
First I checked the different types of power infrastructure that exist in OSM. According to the documentation, the key for these features is “power”. Thus, I ran the following query and got following results:  
    `SELECT DISTINCT value FROM nodes\_tags WHERE key == 'power';`
  
Result: 
`pole
transformer
substation
generator
portal
heliostat
switch
cable\_distribution\_cabinet`

I counted the numbers of generators and substations:
   `SELECT COUNT(*) FROM nodes_tags WHERE key == "power" and value == "generator";
    12
    SELECT COUNT(\*) FROM nodes\_tags WHERE key == "power" and value == "substation";
    111`
    
I explored the fuel source of the generators and saw that some of them were fossil fuel driven and others – renewable:
  `SELECT * FROM nodes\_tags WHERE id IN (SELECT id FROM nodes\_tags WHERE key == "power" and value == "generator") AND key == "source";`

Result: 
`1852185333|source|solar|generator
2251283199|source|hydro|generator
2251283200|source|hydro|generator
2251283201|source|hydro|generator
2251283202|source|hydro|generator
2251283203|source|hydro|generator
4264705104|source|gas|generator
4268835889|source|gas|generator
4328509636|source|gas|generator
4328509637|source|oil|generator`

As far as power substations are concerned, I checked their prevalent voltage levels:
`SELECT * FROM nodes\_tags WHERE id IN (SELECT id FROM nodes\_tags WHERE key == "power" and value == "substation") and key == 'voltage';`
For the economy of space, I am not pasting the output here, however, I saw that the vast majority of substations host transformers which step down voltage from 10kV to 0.4kV. Three larger substations were also listed, with 35kV / 10 kV stepdown levels. 


## Reflection 

This project has been very useful and educative. I’ve understood XML format, learnt XML parsing principles and tools, practiced a lot of Python in the process of designing and running data cleaning and correction codes, refreshed the knowledge of relational databases and SQL queries, learnt how to interact with SQL databases through Python. I’ve managed to run a number of interesting queries, rediscover familiar things and learn new ones about a city I have known well.

The project was also quite tough. Thinking though and writing data auditing / cleaning code in Python was challenging. Understanding OSM structure and relations between different types of nodes, etc., took time and effort. Handling large OSM files was difficult – I did my work on a remote AWS Linux server and I had to upgrade the size of the instance twice before it managed to handle the parsing of the full OSM XML file. Unicode text was tricky to process – initially, I had no knowledge of working with it but the materials I found about this topic on Udacity Forum helped me a lot.

There is a lot of room for the improvement of the data retrieved from OSM XML and making the analysis more advanced. One domain which became obvious to me in the process of work on the project was the quality of values (“v”) data in “node” and “way” tags. The key issue is that many cases, the same thing is spelled in several different ways, which makes grouping and aggregating impossible. The bank names case I described earlier in the document was quite illustrative – because of multiple spellings, I did not manage to do the grouping and aggregation and answer the question of how many ATMs belong to each bank in the city. I believe it would be a huge and probably unjustified task to harmonize all the values (“v”) data in the OSM file but on a case-by-case, as-required basis, i.e. for answering specific questions such as the bank / ATM one, it is possible to formulate regular expressions and write and execute a code that will harmonize the values.

The use of regexes will definitely help with the standardization of bank names. However, the differences in spellings and many types of unexpected typing errors I believe make it impossible to rely on regexes and fully programmatic string substitution. I think fair amount of checking and manual definition of correction dictionaries will be in order. The presence of two and sometimes three languages (Ukrainian, Russian, English) in which the name of the same bank is written in different nodes, further complicates the issue and generates more manual work. So, while I don’t believe the clean-up would take up material computational resources, it is bound to require significant manual, repetitive work.
