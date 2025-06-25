
import datetime
import urllib.request
import json
import copy
import cocparm
from utils.logger_config import setup_logging
from utils.get_secret import get_secret_from_secret_manager_auto

from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms.fields import DateField
from wtforms.validators import DataRequired
from wtforms import validators, SubmitField


app_logger = setup_logging()

app = Flask(__name__)

app.secret_key = get_secret_from_secret_manager_auto('app_secret_key')

coc_data_service_url = get_secret_from_secret_manager_auto('coc_data_service_url')

class InfoForm(FlaskForm):
    playerdate = DateField('End Date', format='%Y-%m-%d', validators=(validators.DataRequired(),))
    submit = SubmitField('End Date')

def read_from_coc(urlAddress):
    data = ""
    try:
        req = urllib.request.Request(urlAddress)
        req.add_header('Accept', 'application/json')
        r = urllib.request.urlopen(req)
        resp = r.read()
        data = json.loads(resp)
    except urllib.error.URLError as e:
        print (e)
    except Exception as e:
        print (e.__doc__)
        print ('read_from_coc exception error')
    return data

@app.route('/test', methods=['GET', 'POST'])
def test():
    form = InfoForm()
    if form.validate_on_submit():
        session['startdate'] = form.startdate.data
        session['enddate'] = form.enddate.data
        return redirect(url_for('date'))
    return render_template('test.html', form=form)

@app.route('/date', methods=['GET', 'POST'])
def date():
    startdate = session['startdate']
    enddate = session['enddate']
    return render_template('date.html')

@app.route('/clan')
def clan():
    app_logger.info("Received clan info request") 
    UserAgent = request.headers.get('User-Agent')
    # print (UserAgent)
    ClanTagList = cocparm.ClanTagList
    cocdata = []
    for ClanTag in ClanTagList:
        data = read_from_coc(coc_data_service_url + '/CWLlist?ClanTag=' + ClanTag)
        # print (type(data))
        cocdata.append( data )
    return render_template('clan.html', ThisHTML="clan", ClanData=cocdata)

@app.route('/player', methods=['GET', 'POST'])
def player():
    PlayerMetric = ['warStars', 'attackWins', 'donations', 'donationsReceived']
    PlayerTag = request.args.get('PlayerTag')
    DateRange = request.args.get('DateRange')
    #if DateRange == '30':
    #    DateRange = '30'
    #elif DateRange == '60':
    #    DateRange = '60'
    #else:
    #    DateRange = '14'
    DateRange = '90'
    data = ""
    form = InfoForm()
    if PlayerTag:
        if form.validate_on_submit():
            playerdate = form.playerdate.data
            data = read_from_coc(coc_data_service_url + "/player?PlayerTag=" + urllib.parse.quote(PlayerTag) + "&DateRange=" + DateRange + "&From=" + playerdate.strftime("%Y-%m-%d"))
        else:
            data = read_from_coc(coc_data_service_url + "/player?PlayerTag=" + urllib.parse.quote(PlayerTag) + "&DateRange=" + DateRange)
    return render_template('player.html', ThisHTML="player", PlayerData=data, PlayerMetric=PlayerMetric, form=form)

@app.route('/playerprogress', methods=['GET', 'POST'])
def playerprogress():
    PlayerMetric = ['warStars', 'attackWins', 'donations', 'donationsReceived']
    PlayerTag = request.args.get('PlayerTag')
    data = ""
    if PlayerTag:
        data = read_from_coc(coc_data_service_url + "/playerprogress?PlayerTag=" + urllib.parse.quote(PlayerTag))
    return render_template('playerprogress.html', ThisHTML="player", PlayerData=data)


@app.route('/claninfo', methods=['GET', 'POST'])
def claninfo():
    data = ""
    playerdata = {}
    MemberData = {}
    ClanTag = request.args.get('ClanTag')
    if ClanTag:
        data = read_from_coc(coc_data_service_url + "/claninfo?ClanTag=" + ClanTag)
    return render_template('claninfo.html', ClanNameTag=ClanTag, ClanData=data, ThisHTML="clan", MemberData=MemberData)

@app.route('/clanprogress', methods=['POST'])
def clanprogress():
    clantag = request.form.get('ClanTag')
    achievement = request.form.get('achievement')
    if achievement:
        separator = achievement.find(':') - 1
        if separator > 0:
            achievement = achievement[:separator]
    data = ""
    try:
        req = urllib.request.Request(coc_data_service_url + "/clanprogress")
        postdata = {'clantag':clantag, 'achievement':achievement}
        req.add_header('Accept', 'application/json')
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        jsondata = json.dumps(postdata)
        jsondataasbytes = jsondata.encode('utf-8')
        req.add_header('Content-Length', len(jsondataasbytes))
        r = urllib.request.urlopen(req, jsondataasbytes)
        resp = r.read()
        data = json.loads(resp)
    except urllib.error.URLError as e:
        print (e)
    return render_template('clanprogress.html', ThitHTML='clanprogress', ClanData=data)

@app.route('/clanwarlog', methods=['GET', 'POST'])
def clanwarlog():
    ClanTag = request.args.get('ClanTag')
    data = ""
    if ClanTag:
        data = read_from_coc(coc_data_service_url + "/clanwarlog?ClanTag=" + ClanTag)
        data['clan'] = {}
        data['player'] = {}
        for warLog in data['print']:
            if data['warlog'][warLog['endTime'][:8]]['state'] != 'noData':
                for member in data['warlog'][warLog['endTime'][:8]]['clan']['members']:
                    if member['tag'] not in data['clan']:
                        data['clan'][member['tag']] = copy.deepcopy(member)
                        data['player'][member['tag']] = copy.deepcopy(member)
                        data['clan'][member['tag']]['mapPositionSum'] = member['mapPosition']
                        data['clan'][member['tag']]['mapPositionCount'] = 1
                    else:
                        data['clan'][member['tag']]['mapPositionSum'] += member['mapPosition']
                        data['clan'][member['tag']]['mapPositionCount'] += 1
                    if 'attacks' in member:
                        data['clan'][member['tag']][warLog['endTime'][:8] + "-1"] = copy.deepcopy(member['attacks'][0])
                        if len(member['attacks']) > 1:
                            data['clan'][member['tag']][warLog['endTime'][:8] + "-2"] = copy.deepcopy(member['attacks'][1])
                        else:
                            data['clan'][member['tag']][warLog['endTime'][:8] + "-2"] = {}
                    else:
                        data['clan'][member['tag']][warLog['endTime'][:8] + "-1"] = {} 
                        data['clan'][member['tag']][warLog['endTime'][:8] + "-2"] = {}
                for member in data['warlog'][warLog['endTime'][:8]]['opponent']['members']:
                    data['player'][member['tag']] = copy.deepcopy(member)
        data['mapPositionSeq'] = {}
        for membertag in data['clan']:
            data['clan'][membertag]['mapPositionAvg'] = data['clan'][membertag]['mapPositionSum'] / data['clan'][membertag]['mapPositionCount']
            data['mapPositionSeq']["{:04.1f}".format(data['clan'][membertag]['mapPositionAvg']) + membertag] = membertag
        data['mapPositionSeq'] = dict(sorted(data['mapPositionSeq'].items()))
        clandata = read_from_coc(coc_data_service_url + "/claninfo?ClanTag=" + ClanTag)
        for member in clandata['memberList']:
            if member['tag'] not in data['clan']:
                data['mapPositionSeq']['99.9' + member['tag']] = member['tag']
                data['clan'][member['tag']] = {'mapPositionAvg' : 99.9}
                data['clan'][member['tag']]['townhallLevel'] = member['townHallLevel']
                data['clan'][member['tag']]['name'] = member['name']
    dumpdata = json.dumps(data, indent=4).replace("\n", "<br>").replace(" ", "&nbsp;")   
    return render_template('clanwarlog.html', ThisHTML="clanwarlog", ClanWarLog=data, dumpdata=dumpdata)

@app.route('/currentwar', methods=['GET', 'POST'])
def currentwar():
    ClanTag = request.args.get('ClanTag')
    data = ""
    if ClanTag:
        data = read_from_coc(coc_data_service_url + "/currentwar?ClanTag=" + ClanTag)
        if data != "":
            clanWarTeam = {}
            clanWarTeam['clan'] = {}
            clanWarTeam['opponent'] = {}
            clanWarTeam['player'] = {}
            clanWarTeam['order'] = {}
            if data['state'] != 'notInWar':
                for member in data['clan']['members']:
                    clanWarTeam['clan'][member['mapPosition']] = copy.deepcopy(member)
                    clanWarTeam['player'][member['tag']] = copy.deepcopy(member)
                    if 'attacks' in member:
                        for attack in member['attacks']:
                            if 'order' in attack:
                                clanWarTeam['order'][attack['order']] = copy.deepcopy(attack)
                                clanWarTeam['order'][attack['order']]['team'] = 'clan'
                for member in data['opponent']['members']:
                    clanWarTeam['opponent'][member['mapPosition']] = copy.deepcopy(member)
                    clanWarTeam['player'][member['tag']] = copy.deepcopy(member)
                    if 'attacks' in member:
                        for attack in member['attacks']:
                            if 'order' in attack:
                                clanWarTeam['order'][attack['order']] = copy.deepcopy(attack)
                                clanWarTeam['order'][attack['order']]['team'] = 'opponent'
                clanWarTeam['orderSeq'] = sorted(clanWarTeam['order'].keys())
        else:
            flash('Clan War Log not available')
            return redirect(url_for('claninfo', ClanTag=ClanTag))
    else:
        flash('Not In War')
        return redirect(url_for('claninfo', ClanTag=ClanTag))
    dumpdata = json.dumps(clanWarTeam, indent=4).replace("\n", "<br>")    
    return render_template('currentwar.html', ThisHTML="currentwar", ClanWar=data, ClanWarTeam=clanWarTeam, dumpdata=dumpdata)

@app.route('/wardetail', methods=['GET', 'POST'])
def wardetail():
    ClanTag = request.args.get('ClanTag')
    Date = request.args.get('Date')
    data = ""
    clanWarTeam = {}
    clanWarTeam['clan'] = {}
    clanWarTeam['opponent'] = {}
    clanWarTeam['player'] = {}
    clanWarTeam['order'] = {}
    if ClanTag and Date:
        data = read_from_coc(coc_data_service_url + "/wardetail?ClanTag=" + ClanTag + "&Date=" + Date)
        # print (data)
        if data['state'] != 'noData':
            for member in data['clan']['members']:
                clanWarTeam['clan'][member['mapPosition']] = copy.deepcopy(member)
                clanWarTeam['player'][member['tag']] = copy.deepcopy(member)
                if 'attacks' in member:
                    for attack in member['attacks']:
                        if 'order' in attack:
                            clanWarTeam['order'][attack['order']] = copy.deepcopy(attack)
                            clanWarTeam['order'][attack['order']]['team'] = 'clan'
            for member in data['opponent']['members']:
                clanWarTeam['opponent'][member['mapPosition']] = copy.deepcopy(member)
                clanWarTeam['player'][member['tag']] = copy.deepcopy(member)
                if 'attacks' in member:
                    for attack in member['attacks']:
                        if 'order' in attack:
                            clanWarTeam['order'][attack['order']] = copy.deepcopy(attack)
                            clanWarTeam['order'][attack['order']]['team'] = 'opponent'
            clanWarTeam['orderSeq'] = sorted(clanWarTeam['order'].keys())
        else:
            flash('No Data')
            return redirect(url_for('clanwarlog', ClanTag=ClanTag))
    else:
        flash('No Data')
        return redirect(url_for('clanwarlog', ClanTag=ClanTag))
    dumpdata = json.dumps(clanWarTeam, indent=4).replace("\n", "<br>")
    return render_template('currentwar.html', ThisHTML="currentwar", ClanWar=data, ClanWarTeam=clanWarTeam, dumpdata=dumpdata)


@app.route('/supertroops', methods=['GET', 'POST'])
def supertroops():
    ClanTag = request.args.get('ClanTag')
    if ClanTag:
        data = read_from_coc(coc_data_service_url + "/supertroops?ClanTag=" + ClanTag)
        return render_template('supertroops.html', ThisHTML='supertroops', activeSuperTroops=data)

@app.route('/clanwarleague', methods=['GET', 'POST'])
def clanwarleague():
    ClanTag = request.args.get('ClanTag')
    Season = request.args.get('Season')
    data = ""
    if ClanTag:
        if Season:
            data = read_from_coc(coc_data_service_url + "/clanwarleague?ClanTag=" + ClanTag + "&Season=" + Season)
        else:
            data = read_from_coc(coc_data_service_url + "/clanwarleague?ClanTag=" + ClanTag)
        #clanlist = []
        #clandata = {}
        #clandata['clans'] = []
        for clan in data['clans']:
            consolidated_data = {}
            consolidated_member_count = {}
            for member in clan['members']:
                level = member['townHallLevel']
                if level not in consolidated_data:
                    consolidated_data[level] = []
                    consolidated_member_count[level] = 0
                consolidated_data[level].append(member)
                consolidated_member_count[level] = consolidated_member_count[level] + 1
            # clan['consolidated_member'] = consolidated_data
            temp_a = list(consolidated_data.keys())
            temp_a.sort(reverse=True)
            clan['consolidated_member'] = {}
            clan['consolidated_member_count'] = consolidated_member_count
            for townHallLevel in temp_a:
                clan['consolidated_member'][townHallLevel] = consolidated_data[townHallLevel]
            #clandata['clans'].append(clan)
        round = 1
        for round_detail in data['rounds']:
            round_detail['day'] = round
            round = round + 1
    return render_template('clanwarleague.html', ThisHTML="clanwarleague", ClanWar=data)

@app.route('/wartag', methods=['GET', 'POST'])
def wartag():
    ClanTag = request.args.get('ClanTag')
    Season = request.args.get('Season')
    RoundDay = request.args.get('Day')
    if ClanTag and Season and RoundDay:
        data = read_from_coc(coc_data_service_url + "/clanwarleague?ClanTag=" + ClanTag + "&Season=" + Season)
        temp_a = int(RoundDay) - 1
        totalMemberList = {}
        for wartag in data['rounds'][temp_a]['warTags']:
            data['rounds'][temp_a][wartag] = read_from_coc(coc_data_service_url + "/wartag?WarTag=" + wartag[1:] + "&Season=" + data['season'])
            # sort clan member list
            temp_member = {}
            for member in data['rounds'][temp_a][wartag]['clan']['members']:
                temp_member[int(member['mapPosition'])] = member
                totalMemberList[member['tag']] = member
            temp_list = list(temp_member.keys())
            temp_list.sort()
            for i in range( 0,  len(temp_list) ):
                data['rounds'][temp_a][wartag]['clan']['members'][i] = temp_member[temp_list[i]]
            # sort opponent member list
            temp_member = {}
            for member in data['rounds'][temp_a][wartag]['opponent']['members']:
                temp_member[int(member['mapPosition'])] = member
                totalMemberList[member['tag']] = member
            temp_list = list(temp_member.keys())
            temp_list.sort()
            for i in range( 0,  len(temp_list) ):
                data['rounds'][temp_a][wartag]['opponent']['members'][i] = temp_member[temp_list[i]]
            if data['rounds'][temp_a][wartag]['clan']['stars'] > data['rounds'][temp_a][wartag]['opponent']['stars'] or ( data['rounds'][temp_a][wartag]['clan']['stars'] == data['rounds'][temp_a][wartag]['opponent']['stars'] and data['rounds'][temp_a][wartag]['clan']['destructionPercentage'] == data['rounds'][temp_a][wartag]['opponent']['destructionPercentage']) :
                data['rounds'][temp_a][wartag]['result'] = 'win'
    return render_template('wartag.html', ThisHTML='clanwarleague', ClanWar=data, RoundDay=temp_a, totalMemberList=totalMemberList)

@app.route('/cwlteam', methods=['GET', 'POST'])
def cwlteam():
    ClanTag = request.args.get('ClanTag')
    Season = request.args.get('Season')
    data = ""
    if ClanTag:
        if Season:
            data = read_from_coc(coc_data_service_url + "/cwlteam?ClanTag=" + ClanTag + "&Season=" + Season)
        else:
            data = read_from_coc(coc_data_service_url + "/cwlteam?ClanTag=" + ClanTag)
        if 'rounds' in data:
            clanlist = data['clanlist']
            clansummary = data['clansummary']
            dumpdata = json.dumps(clanlist, indent=4).replace("\n", "<br>").replace(" ", "&nbsp;")    
            return render_template('cwlteam.html', ThisHTML="clanwarleague", ClanWar=data, clanlist=clanlist, clansummary=clansummary, dumpdata=dumpdata)
        else:
            return data
            #return 'invalid clantag or season'
    else:
        return 'invalid clantag'

def cwlteam2():
    ClanTag = request.args.get('ClanTag')
    Season = request.args.get('Season')
    data = ""
    if ClanTag:
        if Season:
            data = read_from_coc(coc_data_service_url + "/clanwarleague?ClanTag=" + ClanTag + "&Season=" + Season)
        else:
            data = read_from_coc(coc_data_service_url + "/clanwarleague?ClanTag=" + ClanTag)
        #clanlist = []
        #clandata = {}
        #clandata['clans'] = []
        for clan in data['clans']:
            consolidated_data = {}
            consolidated_member_count = {}
            for member in clan['members']:
                level = member['townHallLevel']
                if level not in consolidated_data:
                    consolidated_data[level] = []
                    consolidated_member_count[level] = 0
                consolidated_data[level].append(member)
                consolidated_member_count[level] = consolidated_member_count[level] + 1
            # clan['consolidated_member'] = consolidated_data
            temp_a = list(consolidated_data.keys())
            temp_a.sort(reverse=True)
            clan['consolidated_member'] = {}
            clan['consolidated_member_count'] = consolidated_member_count
            for townHallLevel in temp_a:
                clan['consolidated_member'][townHallLevel] = consolidated_data[townHallLevel]
            #clandata['clans'].append(clan)
        round = 1
        for round_detail in data['rounds']:
            round_detail['day'] = round
            round = round + 1
        clanlist = {}    
        attack = { 1 : {}, 2 : {}, 3 : {}, 4 : {}, 5 : {}, 6 : {}, 7 : {} }
        for clan in data['clans']:    
            memberlist = {}
            for member in clan['members']:
                memberlist[member['tag']] = member
                memberlist[member['tag']]['attack'] = copy.deepcopy(attack)
            clanlist[clan['tag']] = {}
            clanlist[clan['tag']]['name'] = clan['name']
            clanlist[clan['tag']]['memberlist'] = copy.deepcopy(memberlist)
        # move attack data from wartag to member in memberlist of each clan in clanlist    
        for round_detail in data['rounds']:
            for wartag in round_detail['warTags']:
                if wartag != "#0":
                    wartagdata = read_from_coc(coc_data_service_url + "/wartag?WarTag=" + wartag[1:] + "&Season=" + data['season'])
                    for member in wartagdata['clan']['members']:
                        clanlist[wartagdata['clan']['tag']]['memberlist'][member['tag']]['attack'][round_detail['day']] = copy.deepcopy(member)
                    for member in wartagdata['opponent']['members']:
                        clanlist[wartagdata['opponent']['tag']]['memberlist'][member['tag']]['attack'][round_detail['day']] = copy.deepcopy(member)
        # work out each member mapposition and its sequence                
        for clantag in clanlist:
            memberseq = {}
            lastposition = len(clanlist[clantag]['memberlist']) + 1
            for membertag in clanlist[clantag]['memberlist']:
                mapposition = 0
                for attackseq in clanlist[clantag]['memberlist'][membertag]['attack']:
                    if mapposition == 0:
                        # print (clanlist[clantag]['memberlist'][membertag]['attack'][attackseq])
                        if 'mapPosition' in clanlist[clantag]['memberlist'][membertag]['attack'][attackseq]:
                            mapposition = clanlist[clantag]['memberlist'][membertag]['attack'][attackseq]['mapPosition']
                            clanlist[clantag]['memberlist'][membertag]['mapPosition'] = int(mapposition)
                            while mapposition in memberseq:
                                mapposition = mapposition + 0.1
                            memberseq[mapposition] = membertag
                if mapposition == 0:
                    mapposition = lastposition + 1
                    lastposition = lastposition + 1
                    memberseq[mapposition] = membertag
            clanlist[clantag]['memberseq'] = copy.deepcopy(memberseq)
            clanlist[clantag]['sortedMemberSeq'] = sorted(clanlist[clantag]['memberseq'])
            # print (memberseq)
            # print (sorted(memberseq))
        clansummary = copy.deepcopy(clanlist['#' + ClanTag])
        clansummary['tag'] = '#' + ClanTag
        for membertag in clansummary['memberlist']:
            totalstar = 0
            attackcount = 0
            totalpercentage = 0
            for rounds in clansummary['memberlist'][membertag]['attack']:
                if 'mapPosition' in clansummary['memberlist'][membertag]['attack'][rounds]:
                    attackcount += 1
                    if 'attacks' in clansummary['memberlist'][membertag]['attack'][rounds]:
                        totalstar += int(clansummary['memberlist'][membertag]['attack'][rounds]['attacks'][0]['stars'])
                        totalpercentage += int(clansummary['memberlist'][membertag]['attack'][rounds]['attacks'][0]['destructionPercentage'])
            clansummary['memberlist'][membertag]['attackcount'] = attackcount
            clansummary['memberlist'][membertag]['totalstar'] = totalstar
            clansummary['memberlist'][membertag]['totalpercentage'] = totalpercentage
            if attackcount == 0:
                clansummary['memberlist'][membertag]['averagestar'] = 0 
                clansummary['memberlist'][membertag]['averagepercentage'] = 0 
            else:    
                clansummary['memberlist'][membertag]['averagestar'] = "{:5.2f}".format(totalstar / attackcount)
                clansummary['memberlist'][membertag]['averagepercentage'] = "{:5.2f}".format(totalpercentage / attackcount)
            

 
        dumpdata = json.dumps(clansummary, indent=4).replace("\n", "<br>")    
    return render_template('cwlteam.html', ThisHTML="clanwarleague", ClanWar=data, dumpdata=dumpdata, clanlist=clanlist, clansummary=clansummary)

@app.route('/clantroops', methods=['GET', 'POST'])
def clantroops():
    data = ""
    ClanTag = request.args.get('ClanTag')
    if ClanTag:
        data = read_from_coc(coc_data_service_url + "/clantroops?ClanTag=" + ClanTag)
    return render_template('clantroops.html', ClanNameTag=ClanTag, ClanData=data, ThisHTML="clan", heroeslist=cocparm.heroeslist, heroequipmentslist=cocparm.heroequipmentslist, petslist=cocparm.petslist, siegemachinelist=cocparm.siegemachinelist, troopslist=cocparm.troopslist, darktroopslist=cocparm.darktroopslist, spellslist=cocparm.spellslist, icon=cocparm.icon, troopsdetail=cocparm.troopsdetail)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
