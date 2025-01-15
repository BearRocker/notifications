import sqlite3
import dateutil.parser
from LPRarser.LPRequest import LPRequest
from datetime import datetime
from dateutil import parser
import dateutil.tz as dtz
import pytz
import datetime as dt
import collections
from datetime import timedelta
import pandas as pd
import asyncio


def tz_diff(date, tz1, tz2):
    date = pd.to_datetime(date)
    return (tz1.localize(date) -
            tz2.localize(date).astimezone(tz1)).seconds/3600


def is_today_before_date_range(date_range):
    try:
        start_date, end_date = date_range.split(' - ')
        if len(end_date.split(" ")) < 3:
            end_date = start_date.split(" ")[0] + " " + end_date
        end_date = parser.parse(end_date)
        today = datetime.today()
        return today <= end_date
    except dateutil.parser.ParserError:
        return True
    except ValueError:
        if type(date_range) is int:
            end_date = date_range
            if "??" in date_range:
                return True
            end_date = parser.parse(end_date)
            today = datetime.today()
            return today <= end_date
        else:
            return True


class DOTA2:
    def __init__(self, appname):
        self.appname = appname
        self.liquipedia = LPRequest(appname, "dota2")
        self.timezones = collections.defaultdict(list)
        for name in pytz.all_timezones:
            timezone = dtz.gettz(name)
            try:
                now = dt.datetime.now(timezone)
            except ValueError:
                # dt.datetime.now(dtz.gettz('Pacific/Apia')) raises ValueError
                continue
            abbrev = now.strftime('%Z')
            self.timezones[abbrev].append(name)

    async def get_tournament(self):
        connection = sqlite3.connect("../DataBases/CopyBotDB.db")
        cursor = connection.cursor()
        tournaments = []
        tournaments_name = []
        tournaments_names = []
        soup, __ = self.liquipedia.parse('Portal:Tournaments')
        tables = soup.find_all('div', class_="gridTable tournamentCard NoGameIcon")
        tournaments_db = cursor.execute('SELECT Tournament, Game FROM TournamentsInfo')
        tournaments_db = tournaments_db.fetchall()
        tournaments_db_names = []
        for i in tournaments_db:
            tournaments_db_names.append(i[0])
        for table in tables:
            rows = table.find_all('div', class_="gridRow")
            for row in rows:
                tournament = {}
                tournament_name = row.find("div", class_="gridCell Tournament Header")
                tournament_tier = row.find("div", class_="gridCell Tier Header")
                tournament_date = row.find("div", class_="gridCell EventDetails Date Header")
                tournament_prize = row.find("div", class_="gridCell EventDetails Prize Header")
                tournament_teamscount = row.find('div', class_="gridCell EventDetails PlayerNumber Header")
                tournament["tier"] = tournament_tier.get_text()
                tournament["tournament"] = tournament_name.get_text().replace('\xa0', '')
                tournaments_name.append(tournament["tournament"])
                if is_today_before_date_range(tournament_date.get_text()):
                    tournament["date"] = tournament_date.get_text()
                else:
                    continue
                if tournament_prize:
                    tournament["prize"] = tournament_prize.get_text()
                else:
                    tournament["prize"] = 0
                teams_on_tournament = tournament_teamscount.get_text()[0:3]
                teams_on_tournament = teams_on_tournament.replace(u"\xa0", u"")
                if len(teams_on_tournament) >= 2:
                    tournament["teams_count"] = teams_on_tournament
                else:
                    tournament["teams_count"] = "idk"
                tournaments.append(tournament)
                print(tournament['tournament'])
                if tournament['tournament'] not in tournaments_db_names:
                        cursor.execute(
                            'INSERT INTO TournamentsInfo (Game, Tournament, Tier, Prize, TeamsCount) VALUES (?, ?, ?, ?, ?)',
                            ('DOTA2', tournament['tournament'], tournament['tier'], tournament['prize'],
                            tournament['teams_count']))
        for tournament_db in tournaments_db:
            if tournament_db[0] not in tournaments_names and tournament_db[1] == 'DOTA2':
                cursor.execute('DELETE FROM TournamentsInfo WHERE Tournament = ?', (tournament_db[0],))
        connection.commit()
        connection_main = sqlite3.connect('../DataBases/NotificationBotDB.db')
        cursor_main = connection_main.cursor()
        cursor_main.execute('DELETE FROM TournamentsInfo WHERE Game = ?', ('DOTA2',))
        tournaments_db_main = cursor.execute("SELECT * FROM TournamentsInfo")
        tournaments_db_main = tournaments_db_main.fetchall()
        for tournament in tournaments_db_main:
            if tournament[0] == 'DOTA2':
                cursor_main.execute(
                    'INSERT INTO TournamentsInfo (Game, Tournament, Tier, Prize, TeamsCount) VALUES (?, ?, ?, ?, ?)',
                    (tournament[0], tournament[1], tournament[2], tournament[3], tournament[4]))
        connection_main.commit()
        connection.close()
        connection_main.close()
        return tournaments

    async def get_matches(self):
        games = []
        tournaments = []
        soup, __ = self.liquipedia.parse('Liquipedia:Upcoming_and_ongoing_matches')
        table = soup.find_all('table', class_='wikitable wikitable-striped infobox_matches_content')
        for match in table:
            game = {}
            game_time = match.find("span", class_="timer-object timer-object-countdown-only")
            game_tournament = match.find("div", class_="tournament-text-flex")
            date_string, tz_string = game_time.get_text().rsplit(' ', 1)
            if (datetime.today() - parser.parse(date_string)) <= timedelta(days=2, hours=12):
                date = datetime.strptime(date_string, "%B %d, %Y - %H:%M")
                tz_needed = pytz.timezone("Asia/Yekaterinburg")
                if tz_string == "PET":
                    tz = pytz.timezone(self.timezones['CDT'][0])
                    date_res = date + timedelta(hours=tz_diff(date, tz, tz_needed))
                elif tz_string == "SGT":
                    tz = pytz.timezone(self.timezones['+08'][0])
                    date_res = date + timedelta(hours=tz_diff(date, tz, tz_needed))
                else:
                    tz = pytz.timezone(self.timezones[tz_string][0])
                    date_res = date + timedelta(hours=tz_diff(date, tz, tz_needed))
                game['time'] = date_res.strftime("%B %d, %Y - %H:%M")
                urls = game_tournament.find_all('a')
                for a in urls:
                    url = a.get('href').split('/')
                    if len(url) > 3:
                        if '/'.join(url[2:]) not in tournaments:
                            try:
                                tournaments.append('/'.join(url[2:]))
                                tournament_name, __ = self.liquipedia.parse('/'.join(url[2:]))
                                name = tournament_name.find('div', class_="infobox-header wiki-backgroundcolor-light")
                                game['tournament'] = name.get_text()[6:]
                                games.append(game)
                                await asyncio.sleep(30)
                            except Exception as e:
                                tournaments.append('/'.join(url[2:-1]))
                                tournament_name, __ = self.liquipedia.parse('/'.join(url[2:-1]))
                                name = tournament_name.find('div', class_="infobox-header wiki-backgroundcolor-light")
                                game['tournament'] = name.get_text()[6:]
                                games.append(game)
                                await asyncio.sleep(30)
                    else:
                        if url[2] not in tournaments:
                            tournaments.append(url[2])
                            tournament_name, __ = self.liquipedia.parse(url[2])
                            name = tournament_name.find('div', class_="infobox-header wiki-backgroundcolor-light")
                            game['tournament'] = name.get_text()[6:]
                            games.append(game)
                            await asyncio.sleep(30)
        return games



