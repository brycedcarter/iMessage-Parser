# coding=utf-8
import sqlite3
import os
# copy chat.db from ~/Library/Messages/ to the desktop
import datetime
import shutil
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
import seaborn
import loadingBar
import numpy as np

# USER INPUT VARS
THERE_ID = '+15183898984'
REFRESH_DB = False

THEIR_NAME = 'Janice'
MY_NAME = 'Bryce'

iMessagePath = os.path.join(os.path.expanduser('~'),'Library/Messages/')
workingDir = os.path.join(os.path.expanduser('~'),'Desktop/iMessageParserWorkingDir')

currentFigureNumber = 0

def setUpDataSource():
    """
    Creates a copy of the user's iMessage history and returns a sqlite3 cursor object linked to the db
    :return: sqlite3 cursor object linked to the db
    """


    if REFRESH_DB:
        shutil.rmtree(workingDir)
        shutil.copytree(iMessagePath, workingDir)

    dbPath = os.path.join(workingDir,'chat.db')
    conn = sqlite3.connect(dbPath)
    return conn.cursor()

c = setUpDataSource()

# PHRASES = ['love', 'miss', 'care', 'erin', 'noah', '<3', ':P', 'Aww', 'me', 'you', 'yes', 'no', ':)', ':(']


# Query to get the chat ids of the chats that include only the person with the identifier given by THERE_ID
CHAT_QUERY = '''
select chatRowId from
(select chat.ROWID as chatRowId,count(*) as numberOfPeopleInChat
from chat inner join chat_handle_join on chat.ROWID=chat_handle_join.chat_id inner join handle on handle.ROWID=chat_handle_join.handle_id
where chat.ROWID in
(select chat.ROWID
from handle inner join chat_handle_join on handle.ROWID=chat_handle_join.handle_id inner join chat on chat.ROWID=chat_handle_join.chat_id
where handle.id="{0}")
group by chat.ROWID
)
where numberOfPeopleInChat = 1
'''.format(THERE_ID)

c.execute(CHAT_QUERY.format(THERE_ID))
CHAT_IDS = [r[0] for r in c.fetchall()]
print CHAT_IDS

# query to get the messages associated with the chat ids found in the previous query
BASE_QUERY = '''
SELECT *
FROM message LEFT JOIN chat_message_join ON message.ROWID=chat_message_join.message_id LEFT JOIN chat ON chat.ROWID = chat_message_join.chat_id
LEFT JOIN handle ON message.handle_id=handle.ROWID
WHERE chat_message_join.chat_id IN ({0})
AND handle.id is not NULL
'''.format(str(','.join([str(cid) for cid  in CHAT_IDS])))

def loadToMemory():
    c.execute(BASE_QUERY)
    data = [dict(zip(list(map(lambda x: x[0], c.description)), row)) for row in c.fetchall()]
    return data

def getMine(data):
    result = []
    for d in data:
        if d['is_from_me'] == 1:
            result.append({'text': d['text'] if d['text'] is None else d['text'].encode('utf-8'),
                           'sentDate': datetime.datetime.fromtimestamp(d['date']+978264705),
                           'readDate': datetime.datetime.fromtimestamp(d['date_read']+978264705),
                           'sender': 'me'})
    return result


def getTheirs(data):
    result = []
    for d in data:
        if d['is_from_me'] == 0:
            result.append({'text': d['text'] if d['text'] is None else d['text'].encode('utf-8'),
                           'sentDate': datetime.datetime.fromtimestamp(d['date']+978264705),
                           'readDate': datetime.datetime.fromtimestamp(d['date_read']+978264705),
                           'sender': 'them'})
    return result

data = loadToMemory()
mine = getMine(data)
theirs = getTheirs(data)
combined =  sorted(mine+theirs, key=lambda r: r['sentDate'])

def filterForMessagesThatContainText(messages):
    return [m for m in messages if m['text'] is not None]

def prettyPrintMessages(messages):
    maxNameLength = max(len(MY_NAME), len(THEIR_NAME))
    formattedNames = {'me': MY_NAME.ljust(maxNameLength),
                      'them': THEIR_NAME.ljust(maxNameLength)}
    for message in messages:
        print 'From: {2} -- @ {1} : {0}'.format(message['text'], message['sentDate'], formattedNames[message['sender']])

def getWaitingTimeStats(combined, minWaitSeconds=datetime.timedelta(0,30).total_seconds(), maxWaitSeconds=datetime.timedelta(.5).total_seconds()):
    waitingTimes = {'me':[],
                    'them':[]}

    lb = loadingBar.LoadingBar(len(combined))
    for i,message in enumerate(combined):
        lb.update()
        waitFor = 'me' if message['sender'] == 'them' else 'them'
        nextTextsFromOther = [m for m in combined[i:] if m['sender']==waitFor]
        if len(nextTextsFromOther) > 0:
            responseTime = nextTextsFromOther[0]['sentDate'] - message['sentDate']
            waitingTimes[message['sender']].append(float(responseTime.total_seconds()))
        else:
            print message['text']

    filteredWaitingTimes = {}

    filteredWaitingTimes['me'] = [td for td in waitingTimes['me'] if minWaitSeconds < td < maxWaitSeconds]
    filteredWaitingTimes['them'] = [td for td in waitingTimes['them'] if minWaitSeconds < td < maxWaitSeconds]

    return filteredWaitingTimes

def getWordUsageStats(word, combined, variations=()):
    wordUsage = {'me': 0,
                 'them': 0}

    variations = list(variations)
    variations.append(word)
    for person in wordUsage.keys():
        messagesContainingWord = [m for m in combined if m['sender']==person and any([(v.lower() in m['text'].lower()) for v in variations])]
        prettyPrintMessages(messagesContainingWord)
        wordUsage[person] = len(messagesContainingWord)

    return wordUsage

def chunkMessagesByMonth(messages):
    months = sorted(list(set([(m['sentDate'].year, m['sentDate'].month) for m in messages])))
    result = []
    for month in months:
        result.append([m for m in messages if m['sentDate'].year == month[0] and m['sentDate'].month == month[1]])
    return [datetime.datetime(y,m,1) for y,m in months],result

def chunkMessagesByDay(messages):
    days = sorted(list(set([(m['sentDate'].year, m['sentDate'].month, m['sentDate'].day) for m in messages])))
    result = []
    for day in days:
        result.append([m for m in messages if m['sentDate'].year == day[0] and m['sentDate'].month == day[1] and m['sentDate'].day == day[2]])
    return [datetime.datetime(y,m,d) for y,m,d in days],result


def newFigure():
    global currentFigureNumber
    currentFigureNumber += 1
    plt.figure(currentFigureNumber)


def displayWaitingTimesByMonth(saveFig=False):
    newFigure()
    months,messagesForMonths = chunkMessagesByMonth(combined)

    dataToPlot = {'me':[],
                  'them':[]}

    for monthMessages in messagesForMonths:
        waitingTimes = getWaitingTimeStats(monthMessages)
        dataToPlot['me'].append(np.mean(waitingTimes['me'])/60)
        dataToPlot['them'].append(np.mean(waitingTimes['them'])/60)

    plt.plot(months,dataToPlot['me'], label='Me')
    plt.plot(months,dataToPlot['them'], label='Them')
    plt.title('Average Waiting Time By Month')
    plt.xlabel('Month')
    plt.ylabel('Average Waiting Time (min)')
    plt.legend(loc='upper right')

    if saveFig:
        pylab.savefig(os.path.join(workingDir, 'waiting_times_by_month.png'))

def displayWordUsagePerMonth(word, variations=(), saveFig=False):
    newFigure()
    months, messagesForMonths = chunkMessagesByMonth(filterForMessagesThatContainText(combined))

    dataToPlot = {'me': [],
                  'them': [],
                  'me_norm': [],
                  'them_norm': []}

    for monthMessages in messagesForMonths:
        wordUsage = getWordUsageStats(word, monthMessages, variations)
        dataToPlot['me'].append(wordUsage['me'])
        dataToPlot['me_norm'].append(float(wordUsage['me']) / len([m for m in monthMessages if m['sender'] == 'me']))
        dataToPlot['them'].append(wordUsage['them'])
        dataToPlot['them_norm'].append(float(wordUsage['them']) / len([m for m in monthMessages if m['sender'] == 'them']))

    plt.plot(months,dataToPlot['me'], label='Me')
    plt.plot(months,dataToPlot['them'], label='Them')
    plt.title('Number of times using the word "{0}" By Month'.format(word.lstrip()))
    plt.xlabel('Month')
    plt.ylabel('# of "{0}"'.format(word.lstrip()))
    plt.legend(loc='upper right')
    if saveFig:
        pylab.savefig(os.path.join(workingDir, '{0}.png'.format(word.lstrip())))

    newFigure()
    plt.plot(months,dataToPlot['me_norm'], '--', alpha=0.7, label='Me')
    plt.plot(months,dataToPlot['them_norm'], '--', alpha=0.7, label='Them')
    plt.title('Normalized Number of times using the word "{0}" By Month'.format(word.lstrip()))
    plt.xlabel('Month')
    plt.ylabel('(# of "{0}")/(# of messages)'.format(word.lstrip()))
    plt.legend(loc='upper right')
    if saveFig:
        pylab.savefig(os.path.join(workingDir, '{0}_norm.png'.format(word.lstrip())))

# days,messagesForDays = chunkMessagesByDay(combined)
# plt.figure(2)
# dataToPlot = {'me': [],
#               'them': []}
# for dayMessages in messagesForDays:
#     waitingTimes = getWaitingTimeStats(dayMessages)
#     dataToPlot['me'].append(np.mean(waitingTimes['me']) / 60)
#     dataToPlot['them'].append(np.mean(waitingTimes['them']) / 60)
#
# print dataToPlot
# plt.plot(days, dataToPlot['me'], label='Me')
# plt.plot(days, dataToPlot['them'], label='Them')
# plt.legend(loc='upper right')



displayWordUsagePerMonth(' Noah', saveFig=True)
displayWordUsagePerMonth(' Erin', saveFig=True)
displayWordUsagePerMonth(' miss', saveFig=True)
displayWordUsagePerMonth('<3', variations=['❤️'], saveFig=True)
displayWordUsagePerMonth('Aww', saveFig=True)
displayWordUsagePerMonth('happy_face', variations=[':)','😊'], saveFig=True)
displayWordUsagePerMonth('sad_face', variations=[':(','😟'], saveFig=True)
displayWordUsagePerMonth(' Love you', saveFig=True)
# plt.show()
