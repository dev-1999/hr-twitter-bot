# hr-twitter-bot

This repository contains the code necessary run the Twitter bot under the handle [@dinger_rates](https://twitter.com/dinger_rates) that rates the aesthetic impressiveness of MLB home runs.

## Background

A while back, Yordan Alvarez hit [this home run](https://www.mlb.com/video/yordan-alvarez-homers-24-on-a-fly-ball-to-right-field), which was met with outcry on Twitter about how it could have travelled _only_ 415 feet. How what the announcer described as "one of the longest home runs in the history of [Minute Maid Park] would have landed on Tal's Hill (RIP). That's when I decided to write [this article](https://washusportsanalytics.wixsite.com/washusportsanalytics/post/developing-a-metric-to-quantify-home-run-impressiveness) that built a preliminary version of this model.

This bot applies that same goal of rating home runs on how impressive they looks, and uses a random forest model to score each home run hit, and use a star system to classify the 'coolness' of a home run. It scans the MLB API for batted-ball data on new home runs, and then tweets the score, star rating, and other summary statistics (including arc length, not currently available on Baseball Savant).

## The Model

The home run rating is a random forest model using the following features (from most to least important):
 - Distance Delta: The difference between the distance travelled by the batted ball versus the expected distance of a home run hit with the ball's spray angle
 - Hit Distance
 - Distance Delta Percent: The distance travelled by the ball divided by the expected distance based on the ball's spray angle
 - Hit Arc Length
 - Vertical Velocity Component
 - Horizontal Velocity Component
 - Launch Angle

The model was trained on 111 home runs from the 2019 MLB season which I watched and subjectively scored. I tested the model on all home runs from the 2020 season to eyeball its performance - if you're curious the highest rated home run recieved a 9.58 and was [this bomb from Miguel Sano](https://www.mlb.com/astros/video/miguel-sano-s-458-ft-home-run?q=ContentTags%20%3D%20%5B%22playerid-593934%22%5D%20Order%20by%20Timestamp%20DESC&cp=CMS_FIRST).

To improve model interpretability, I broke down the percentile outcomes of score from the 2020 test dataset into buckets for star rating - something loosely inspired by how Statcast measures outfield catch difficulty. These buckets are as follows:

| Percentile |     Score    | Stars   |
|:----------:|:------------:|:-------:|
| [0, 10)    | <3.01        | 0 Stars |
| [10, 30)   | [3.01, 3.93) | 1 Star  |
| [30, 50)   | [3.93, 4.6)  | 2 Stars |
| [50, 70)   | [4.6, 6.42)  | 3 Stars |
| [70, 90)   | [6.42, 7.46) | 4 Stars |
| [90, 100]  | >7.46        | 5 Stars |

Another issue is the non-normal distribution. This following graph shows the scores for all 2020 home runs, with the percentile buckets highlighted:
![Distribution](/images/dist.png)

Considering the subjectivity of the data, having a non-normal input is likely the result of non-normal training data. A goal of this project would be to expand the model by taking input from twitter to train the model, but that's a long ways off. In the meantime, watching and reviewing a more balanced distribution of home runs would be an area for improvement as well.

## The Bot

The script in *api-scan.py* contains the code run as a worker script by Heroku. It imports the random forest model from the training data and then makes a call to the MLB stats API every ~10 seconds. The play ids for each day's previously tweeted home runs are stored in *id_list.txt* to prevent any unforseen crashes of the application from making duplicate tweets. After performing the necessary calculations, the Tweepy library is used to call Twitter's developer API to send a tweet for the home run.

## Odds and Ends
Calculation of Arc Length: https://brilliant.org/discussions/thread/arc-length-of-projectile-2/

Expected distance is modeled by polynomial: *y = 417.09 + 0.337x - 0.028x<sup>2</sup>* where *y* is the predicted distance and *x* is the spray angle, where 45 is pulled down the line, 0 is straightaway centerfield, and -45 is down the opposite field foul line (all regularized by batter handedness).

## Contact
If you have comments or questions or have watched more home runs and want to add to the training dataset, contact me at devlin.s@wustl.edu