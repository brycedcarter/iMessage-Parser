import sqlite3
import os
# copy chat.db from ~/Library/Messages/ to the desktop
import datetime
import matplotlib.pyplot as plt
import seaborn

dbPath = os.path.join(os.path.expanduser('~'),'Desktop/chat.db')
conn = sqlite3.connect(dbPath)
c = conn.cursor()

PHRASES = ['love', 'miss', 'care', 'erin', 'noah', '<3', ':P', 'Aww', 'me', 'you', 'yes', 'no', ':)', ':(']
THERE_ID = '+15183898984'

CHAT_QUERY = '''
SELECT chat.ROWID FROM
chat INNER JOIN chat_handle_join ON chat.ROWID=chat_handle_join.chat_id
INNER JOIN handle ON handle.ROWID=chat_handle_join.handle_id
WHERE handle.id = "{0}"
'''.format(THERE_ID)

c.execute(CHAT_QUERY.format(THERE_ID))
CHAT_IDS = c.fetchall()

BASE_QUERY = '''
SELECT *
FROM message LEFT JOIN chat_message_join ON message.ROWID=chat_message_join.message_id LEFT JOIN chat ON chat.ROWID = chat_message_join.chat_id
LEFT JOIN handle ON message.handle_id=handle.ROWID
WHERE chat_message_join.chat_id IN ({0})
AND handle.id = "{1}"
'''.format(str(','.join([str(i[0]) for i  in CHAT_IDS])), THERE_ID)

print BASE_QUERY

def loadToMemory():
    c.execute(BASE_QUERY)
    data = [dict(zip(list(map(lambda x: x[0], c.description)), row)) for row in c.fetchall()]
    return data

def getMine(data):
    result = []
    for d in data:
        if d['is_from_me'] == 1:
            result.append({'text': d['text'],
                           'sentDate': datetime.datetime.fromtimestamp(d['date_delivered']+978264705),
                           'readDate': datetime.datetime.fromtimestamp(d['date_read']+978264705)})
    return result

def getTheirs(data):
    result = []
    for d in data:
        if d['is_from_me'] == 0:
            result.append({'text': d['text'],
                           'sentDate': datetime.datetime.fromtimestamp(d['date_delivered']+978264705),
                           'readDate': datetime.datetime.fromtimestamp(d['date_read']+978264705)})
    return result

def filterBadData(data):
    result = [d for d in data if d['sentDate']>datetime.datetime.fromtimestamp(1403675026)]
    return result

def groupDataByDay(data):
    days = {}
    for m in data:
        day = m['sentDate'].date()
        if day not in days.keys():
            days[day] = [m]
        else:
            days[day].append(m)
    return days

def getCharOnDay(data):
    result = []
    for day in data.keys():
        print day
        print [len(d['text']) for d in data[day]]
        result.append((day, len([len(d['text']) for d in data[day]])))
    result.sort(key=lambda d: d[0])
    return result

DATA = loadToMemory()

# MINE = getMine(DATA)
# THEIRS = getTheirs(DATA)
MINE = getMine(DATA)
THEIRS = getTheirs(DATA)


for t in MINE:
    print t['text']

# print len(DATA)
print sum([len(m['text']) for m in MINE if m['text'] is not None])
print sum([len(m['text']) for m in THEIRS if m['text'] is not None])

def getStatsForTerm(messages, term):
    textsIncluding = [m for m in [t for t in messages if t['text'] is not None] if term in m['text']]
    return len(textsIncluding), (float(len(textsIncluding))/len(messages))

PROCESS_PHRASES = False
if PROCESS_PHRASES:
    for term in PHRASES:
        rawMine, normMine = getStatsForTerm(MINE, term)
        rawTheirs, normTheirs = getStatsForTerm(THEIRS, term)
        print '==================================='
        print 'Bryce: %s'%term
        print 'Raw = %s'%rawMine
        print 'Normalized = %s' % (normMine/max([normMine, normTheirs]))
        print 'Janice: %s'%term
        print 'Raw = %s' % rawTheirs
        print 'Normalized = %s' % (normTheirs/max([normMine, normTheirs]))


# # plt.plot([d['sentDate'] for d in MINE], [len(d['text']) for d in MINE], 'ro')
# dayData = getCharOnDay(groupDataByDay(THEIRS))
# plt.plot([d[0] for d in dayData], [d[1] for d in dayData], 'g-')
# dayData = getCharOnDay(groupDataByDay(MINE))
# plt.plot([d[0] for d in dayData], [d[1] for d in dayData], 'r-')
# plt.axes().set_xlim([datetime.datetime.fromtimestamp(1403675026), datetime.datetime.now()])
#
# plt.show()