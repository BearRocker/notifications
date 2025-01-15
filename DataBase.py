import asyncio
import sqlite3
from Disciplines.Apex import Apex
from Disciplines.CS2 import CS
from Disciplines.Dota2 import DOTA2
import datetime
from datetime import datetime
from dateutil import parser


async def update_db():
    connection = sqlite3.connect("DataBases/CopyBotDB.db")

    cursor = connection.cursor()

    tournaments = await get_tournament_db()
    for tournament in tournaments:
        if datetime.today() > parser.parse(tournament[-1]):
            cursor.execute("DELETE FROM MatchInfo WHERE Tournament = ?", (tournament[0],))

    apex = Apex(appname="Test")
    cs = CS(appname="Test")
    dota2 = DOTA2(appname="Test")
    dota_matches = await dota2.get_matches()
    for match in dota_matches:
        info = cursor.execute('SELECT * FROM MatchInfo WHERE Tournament=?', (match['tournament'], ))
        if info.fetchone() is None:
            cursor.execute('INSERT INTO MatchInfo (Tournament, Game, MatchTime) VALUES (?, ?, ?)',
                           (match['tournament'], "Dota 2", match['time']))
        else:
            cursor.execute('UPDATE MatchInfo SET MatchTime= ? WHERE Tournament = ? AND Game = ?',
                           (match['time'], match['tournament'], "Dota 2"))
    await asyncio.sleep(60)
    cs_matches = await cs.get_matches()
    for match in cs_matches:
        info = cursor.execute('SELECT * FROM MatchInfo WHERE Tournament=?', (match['tournament'],))
        if info.fetchone() is None:
            cursor.execute('INSERT INTO MatchInfo (Tournament, Game, MatchTime) VALUES (?, ?, ?)',
                           (match['tournament'], "CS2", match['time']))
        else:
            cursor.execute('UPDATE MatchInfo SET MatchTime= ? WHERE Tournament = ? AND Game = ?',
                           (match['time'], match['tournament'], "CS2"))
    await asyncio.sleep(60)
    apex_matches = await apex.get_matches()
    for match in apex_matches:
        info = cursor.execute('SELECT * FROM MatchInfo WHERE Tournament=?', (match['tournament'],))
        if info.fetchone() is None:
            cursor.execute('INSERT INTO MatchInfo (Tournament, Game, MatchTime) VALUES (?, ?, ?)',
                           (match['tournament'], "Apex", match['time']))
        else:
            cursor.execute('UPDATE MatchInfo SET MatchTime= ? WHERE Tournament = ? AND Game = ?',
                           (match['time'], match['tournament'], "Apex"))
    connection.commit()
    connection_main = sqlite3.connect('DataBases/NotificationBotDB.db')
    cursor_main = connection_main.cursor()
    cursor_main.execute('DELETE FROM MatchInfo')
    tournaments = cursor.execute("SELECT * FROM MatchInfo")
    tournaments = tournaments.fetchall()
    for tournament in tournaments:
        cursor_main.execute('INSERT INTO MatchInfo (Tournament, Game, MatchTime) VALUES (?, ?, ?)',
                            (tournament[0], tournament[1], tournament[2]))
    connection_main.commit()
    connection.close()
    connection_main.close()


async def get_tournament_db():
    connection = sqlite3.connect("DataBases/NotificationBotDB.db")
    cursor = connection.cursor()
    tournaments = cursor.execute('SELECT Tournament, MatchTime FROM MatchInfo')
    tournaments = tournaments.fetchall()
    connection.commit()
    connection.close()
    return tournaments