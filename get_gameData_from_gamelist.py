from pantheon import pantheon
import asyncio
import json
import random
import time
import math
import sys
import scipy.stats
import pandas as pd
import re


server = "NA1"
api_key = "RGAPI-e7f1caca-4232-4cf8-ab96-cd3af0dcf6a4"

def requestsLog(url, status, headers):
        print(status)

panth = pantheon.Pantheon(server, api_key, errorHandling=True, requestsLoggingFunction=requestsLog, debug=True)

async def getSummonerId(name):
    try:
        data = await panth.getSummonerByName(name)
        return data['accountId']
    except Exception as e:
        print(e)


async def getMatchList(accountId, time_list):
    try:
        tasks = [panth.getMatchlist(accountId, params = {"queueId":420, "beginTime":i, "endTime":j}) for i,j in time_list]
        return await asyncio.gather(*tasks)
    except Exception as e:
        print(e)

async def getMatchData(gameIds):
    try:
        tasks = [panth.getMatch(gameId) for gameId in gameIds]
        return await asyncio.gather(*tasks)
    except Exception as e:
        print("Attempting Again")
        condition = True
        counter = 1
        while (condition):
            asyncio.sleep(counter)
            try:
                tasks = [panth.getMatch(gameId) for gameId in gameIds]
                return await asyncio.gather(*tasks)
            except Exception as e:
                counter = counter * 2
                print(counter)

def get_gamedata(values, champKey):
    results = dict()
    fields = ['win', 'kills', 'deaths', 'assists', 'totalDamageDealtToChampions', 'damageDealtToObjectives', 'visionScore', 'goldEarned', 
    'totalTimeCrowdControlDealt', 'champLevel', 'totalMinionsKilled', 'neutralMinionsKilled']
    for name in fields:
        results[name] = list()
    for data in values:
        if type(data)!=dict or 'gameId' not in data:
            continue
        results[data['gameId']] = list()
        for i in data['participants']:
            if i['championId']==int(champKey):
                for name in fields:
                    results[name].append(i['stats'][name]) 
    return results

def compare_stats(summoner_data):
    fields = ['win', 'kills', 'deaths', 'assists', 'totalDamageDealtToChampions', 'damageDealtToObjectives', 'visionScore', 'goldEarned', 
    'totalTimeCrowdControlDealt', 'champLevel', 'totalMinionsKilled', 'neutralMinionsKilled']
    stats = pd.read_csv("relevant_data/stats.csv").set_index("Unnamed: 0")
    error = dict()
    for key in summoner_data:
        error[key] = dict()
        for name in fields:
            error[key][name] = list()
            for val in summoner_data[key][name]:
                if name == 'win':
                    val = int(val)
                mean_var = [float(i.strip('[]')) for i in re.split(',', stats.loc[key,name])]
                error[key][name].append((val - mean_var[0])/mean_var[1])
    for key in error:
        for name in fields:
            error[key][name] = scipy.stats.describe(error[key][name])
    return error 

def get_gameData_from_summoner(summoner):

    summoner = str(summoner)

    try:
        with open("summoner_data/" + summoner + "-stats.json") as myfile:
            print("Already exists")
            return
    
    except:

        print("Gathering Data")

        loop = asyncio.get_event_loop() 
        accountId = loop.run_until_complete(getSummonerId(summoner))

        time_list = list()
        beginTime = 1516060800000
        while (beginTime<1542009600000):
            endTime = 7*24*60*60*1000 + beginTime
            time_list.append([beginTime, endTime])
            beginTime = endTime

        match_list = loop.run_until_complete(getMatchList(accountId, time_list))

        champ_game = dict()
        for matches in match_list:
            try:
                for match in matches['matches']:
                    if match['champion'] not in list(champ_game.keys()):
                        champ_game[match['champion']] = list()
                    champ_game[match['champion']].append(match['gameId'])
            except:
                continue
        for key in list(champ_game.keys()):
            if len(champ_game[key])<50:
                del champ_game[key]

        final = dict()
        fields = ['win', 'kills', 'deaths', 'assists', 'totalDamageDealtToChampions', 'damageDealtToObjectives', 'visionScore', 'goldEarned', 
        'totalTimeCrowdControlDealt', 'champLevel', 'totalMinionsKilled', 'neutralMinionsKilled']
        for key in champ_game:
            final[key] = dict()
            for name in fields:
                final[key][name] = list()
        for key in champ_game:
            game_list = champ_game[key]
            while (game_list!=[]):
                games = game_list[0:100]
                data = loop.run_until_complete(getMatchData(games))
                print("WAITING...")
                time.sleep(2)
                result = get_gamedata(data, key)
                [final[key][name].append(val) for name in fields for val in result[name]]
                [game_list.remove(i) for i in games]
            print(key)

        stats = compare_stats(final)
        for key in stats:
            for name in fields:
                stats[key][name] = stats[key][name][2:4]
        name = 'summoner_data/' + str(summoner) + '-stats.json'
        with open(name, 'w+', newline = '') as newfile:
            json.dump(stats, newfile)
        print("CREATED " + name)


if __name__ == "__main__":
    a = sys.argv[1]
    get_gameData_from_summoner(a)



