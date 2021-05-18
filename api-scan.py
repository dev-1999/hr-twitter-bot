#!/usr/bin/env python
# coding: utf-8

# In[31]:


import statsapi
import pandas as pd
import math
#import numpy as np
from sklearn.ensemble import RandomForestRegressor
import datetime
from time import sleep
import tweepy
import pickle
from os import environ
from pytz import timezone

utc = timezone('UTC')
hon = timezone('HST')
curtime = utc.localize(datetime.datetime.now())
hi_time = curtime.astimezone(hon)


# In[32]:


auth = tweepy.OAuthHandler(consumer_key=environ['CONSUMER_KEY'],
                  consumer_secret=environ['CONSUMER_SECRET'])
auth.set_access_token(environ['ACCESS_KEY'],environ['ACCESS_SECRET'])
api = tweepy.API(auth)


# In[33]:


#returns arc length in feet
#inputs: exit velo in MPH, launch angle in degrees
def calculate_arc_length(exit_velo,launch_angle):
    def secant(x):
        return 1/(math.cos(x))
    la_radians = math.radians(launch_angle)
    ev_fps = exit_velo * 5280 / 3600
    g = 32.17
    arc_length = (ev_fps*math.cos(la_radians))**2/(2*g)*(2*secant(la_radians)*math.tan(la_radians) +                                                         math.log(abs((1 + math.sin(la_radians))/(1-math.sin(la_radians)))))
    return arc_length


# In[34]:


regr = pickle.load(open('hr_model.sav', 'rb'))
ols = pickle.load(open('hr_model_2.sav', 'rb'))
#Ax^2 + Bx + C
poly_coef = [-2.80046667e-02,  3.36567616e-01,  4.17068690e+02]


# In[35]:


def check_todays_games(game_list):
    for game in game_list:
        topData = statsapi.get('game', {'gamePk':game})
        allPlays = topData['liveData']['plays']['allPlays']
        for play in allPlays:
            try:
                if play['result']['eventType'] == 'home_run':
                    play_id = (play['playEvents'][-1]['playId'])
                    if play_id in play_id_list:
                        pass
                    else:
                        play_id_list.append(play_id)
                        desc_list.append(play['result']['description'])
                        player_list.append(play['matchup']['batter']['fullName'])
                        hitData = (play['playEvents'][-1]['hitData'])
                        stands_list.append(play['matchup']['batSide']['code'])
                        #print(play['result']['description'])
                        hit_distance_list.append(hitData['totalDistance'])
                        launch_speed_list.append(hitData['launchSpeed'])
                        launch_angle_list.append(hitData['launchAngle'])
                        hcx_list.append(hitData['coordinates']['coordX'])
                        hcy_list.append(hitData['coordinates']['coordY'])
                        #print("--")
            except KeyError:
                pass


# In[36]:


def tweet_wrapper(ind):
    stars = ""
    score = todays_df.loc[ind,'score']
    for thresh in [3,4,5,6.42,7.46]:
        if score > thresh:
            stars = stars + "⭐"
    if stars == "":
        stars = "💤"
    string = "DINGER ALERT: \n" +              todays_df.loc[ind,'desc'] + "\n" +              "Arc Length: " + str(round(todays_df.loc[ind,'arc_length'],1)) + " feet | Exit Velo: " +              str(todays_df.loc[ind,'launch_speed']) + " MPH | Distance: " + str(todays_df.loc[ind,'hit_distance']) + " feet\n" +              "Grade: " + str(round(score, 2)) +"/10 | No Doubt Rating: " + str(stars)# + " Stars \n" #+ \
             #str(todays_df.loc[ind,'score'])
    return string


# In[37]:

#Read in previous tweets
id_list = []
idfile = open('id_list.txt','r')
for line in idfile:
    id_list.append(line.strip('\n'))
idfile.close()

today_string = hi_time.strftime("%m/%d/%Y")
daygames = statsapi.schedule(date=today_string)
game_list = [daygames[i]['game_id'] for i in range(len(daygames))]


# In[17]:

#Check to see potential reset
if len(id_list) > 0:
    if id_list[0] != today_string:
        idfile = open('id_list.txt','w')
        idfile.write(today_string)
        id_list = []
        idfile = open('id_list.txt','r')
        for line in idfile:
            id_list.append(line)
        idfile.close()


#Main Loop:
#
tweeted_ids = []
tweet_links = []
play_id_list = []
player_list = []
desc_list = []
hit_distance_list = []
launch_speed_list = []
launch_angle_list = []
hcx_list = []
hcy_list = []
stands_list = []
while True:
    check_todays_games(game_list)
    adjpull_angle_list = []
    for i in range(len(hcx_list)):
        x = math.atan((hcx_list[i] - 125.42)/(198.27 - hcy_list[i]))
        if stands_list[i] == 'L':
            adjpull_angle_list.append(x*360/(2*math.pi))
        else:
            adjpull_angle_list.append(x*360/(2*math.pi)*-1)
    #'yhat_angle_pct', 'Vy', 'Vx'
    yhat_angle_pct_list = []
    yhat_delta_list = []
    for i in range(len(adjpull_angle_list)):
        yhat = 0
        for j in range(3):
            yhat += adjpull_angle_list[i]**(2-j) * poly_coef[j]
        yhat_angle_pct_list.append(yhat/hit_distance_list[i])
        yhat_delta_list.append(hit_distance_list[i] - yhat)
    Vy_list = [launch_speed_list[i] * math.sin(launch_angle_list[i]*2*math.pi/360) for i in range(len(launch_angle_list))]
    Vx_list = [launch_speed_list[i] * math.cos(launch_angle_list[i]*2*math.pi/360) for i in range(len(launch_angle_list))]
    arc_length_list = [calculate_arc_length(launch_speed_list[i],launch_angle_list[i]) for i in range(len(launch_angle_list))]
    spray_dist_list = [adjpull_angle_list[i] * hit_distance_list[i] for i in range(len(adjpull_angle_list))]
    todays_df = pd.DataFrame.from_dict(data={'id':play_id_list,'batter':player_list,'desc':desc_list, 'launch_speed':launch_speed_list,
    'hit_distance':hit_distance_list,'launch_angle':launch_angle_list,'hcx':hcx_list,'hcy':hcy_list,
    'stand':stands_list, 'adjpull_angle':adjpull_angle_list,'yhat_angle_pct':yhat_angle_pct_list,
                                        'Vy':Vy_list,'Vx':Vx_list, 'arc_length':arc_length_list, 'spray_dist':spray_dist_list,
                                            'yhat_delta':yhat_delta_list})
    if len(todays_df) > 0:
        y_pred_list = regr.predict(todays_df[['hit_distance', 'launch_angle', 'yhat_delta', 'yhat_angle_pct', 'Vy', 'Vx', 'arc_length']])
        todays_df['score'] = y_pred_list
        todays_df['ols'] = ols.predict(todays_df[['arc_length','hit_distance','yhat_angle_pct']])
        for ind in todays_df.index.tolist():
            if todays_df.loc[ind, 'id'] in tweeted_ids:
                pass
            else:
                tweet = (tweet_wrapper(ind))
                tweet_links.append(api.update_status(tweet))
                print(tweet)
                print(datetime.datetime.now().strftime("%H:%M:%S"))
                tweeted_ids.append(todays_df.loc[ind, 'id'])
                idfile = open('id_list.txt', 'a')
                idfile.write("\n" + todays_df.loc[ind, 'id'])
                idfile.close()
    else:
        pass
    sleep(8)
    print("Updated as of: " + datetime.datetime.now().strftime("%H:%M:%S"))


# In[40]:


#TODO put script into tweepy update_status
#https://docs.tweepy.org/en/latest/api.html
todays_df['game_date'] = [today_string for i in range(len(todays_df))]
todays_df['link'] = ["https://baseballsavant.mlb.com/sporty-videos?playId=" + str(i) for i in todays_df['id'].tolist()]
todays_df[['game_date','batter','id','desc','hcx','hcy','hit_distance','launch_speed','launch_angle','adjpull_angle','ols','stand','score','link']].to_csv('test.csv')

