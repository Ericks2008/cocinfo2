from flask import Blueprint, render_template, request, current_app, flash
import urllib.parse
import copy
import json
import traceback
from utils.helper import get_level_badge_class

clan_bp = Blueprint('clan_bp', __name__)

@clan_bp.route('/clan')
def clan():
    current_app.app_logger.info("Received clan info request")
    ClanTagList = current_app.cocinfo_cocparm['cocinfo_clan_list']

    cocdata = []
    for ClanTag in ClanTagList:
        try:
            data = current_app.coc_api_client.get_cwl_list(ClanTag)
            if data:
                cocdata.append(data)
            else:
                current_app.app_logger.warning(f"No data returned for ClanTag: {ClanTag}")
        except Exception as e:
            current_app.app_logger.error(f"Error fetching CWL list for {ClanTag}: {e}")
            flash(f"Failed to load data for clan {ClanTag}. Please try again later.", "error")
    return render_template('clan.html', ThisHTML="clan", ClanData=cocdata, 
                           cocparm=current_app.cocinfo_cocparm)

@clan_bp.route('/clan/<string:clan_tag>/info')
def get_clan_details(clan_tag:None):
    # get_clan_details replace claninfo
    data = current_app.coc_api_client.get_clan_details(clan_tag)
    return render_template('claninfo.html', ClanNameTag=clan_tag, ClanData=data, ThisHTML="clan",
                           cocparm=current_app.cocinfo_cocparm,)


@clan_bp.route('/clan/<clan_tag>/supertroops', methods=['GET'])
def supertroops(clan_tag):
    data = current_app.coc_api_client.get_clan_supertroops(clan_tag)
    return render_template('supertroops.html', ThisHTML='supertroops', ClanData=data,
                           cocparm=current_app.cocinfo_cocparm,)


@clan_bp.route('/clan/<clan_tag>/troops', methods=['GET'])
def display_clan_troops(clan_tag):
    clan_data = None # Initialize
    try:
        clan_data = current_app.coc_api_client.get_clan_troops(clan_tag) 
        if clan_data and 'error' in clan_data:
            flash(f"Error fetching clan troops data: {clan_data['error']}", 'danger')
            clan_data = None
        elif not clan_data:
            flash(f"Could not retrieve clan troops data for tag: {clan_tag}.", 'warning')
    except Exception as e:
        current_app.logger.error(f"Error calling clan troops API for {clan_tag}: {e}")
        flash("An unexpected error occurred while fetching clan troops data. Please try again later.", 'danger')
        clan_data = None

    return render_template(
        'clantroops.html',
        ClanNameTag=clan_tag,
        ClanData=clan_data,
        ThisHTML="clan",
        get_level_badge_class=get_level_badge_class,
        cocparm=current_app.cocinfo_cocparm
    )

@clan_bp.route('/clan/<clan_tag>/progress', methods=['GET'])    
def display_clan_progress(clan_tag):
    achievement = request.args.get('achievement')
    if achievement:
        achievement = achievement.split(':', 1)[0].strip()

    try:
        clan_data = current_app.coc_api_client.get_clan_progress(clan_tag, achievement) 
        if clan_data and 'error' in clan_data:
            flash(f"Error fetching clan troops data: {clan_data['error']}", 'danger')
            clan_data = None
        elif not clan_data:
            flash(f"Could not retrieve clan troops data for tag: {clan_tag}.", 'warning')
    except Exception as e:
        current_app.logger.error(f"Error calling clan troops API for {clan_tag}: {e}")
        flash("An unexpected error occurred while fetching clan troops data. Please try again later.", 'danger')
        clan_data = None
    return render_template('clanprogress.html', ThitHTML='clanprogress', ClanData=clan_data,
                           cocparm=current_app.cocinfo_cocparm)


@clan_bp.route('/clan/currentwar/<clan_tag>', methods=['GET'])
def display_currentwar(clan_tag: str):
    war_data = None
    clan_war_team = None
    try:
        war_data = current_app.coc_api_client.get_current_war(clan_tag)
        if war_data and 'error' in war_data:
            flash(f"Error fetching current war data: {war_data['error']}", 'danger')
            war_data = None
        elif not war_data:
            flash(f"Could not retrieve current war data for tag: {clan_tag}.", 'warning')
        else:
            clan_war_team = {
                    'clan': {},
                    'opponent': {},
                    'player': {},
                    'order': {}
                }
            if war_data['state'] != 'notInWar':
                for group in ['clan', 'opponent']:
                    for member in war_data[group]['members']:
                        clan_war_team[group][member['mapPosition']] = copy.deepcopy(member)
                        clan_war_team['player'][member['tag']] = copy.deepcopy(member)
                        if 'attacks' in member:
                            for attack in member['attacks']:
                                if 'order' in attack:
                                    clan_war_team['order'][attack['order']] = copy.deepcopy(attack)
                                    clan_war_team['order'][attack['order']]['team'] = group
                clan_war_team['orderSeq'] = sorted(clan_war_team['order'].keys())
    except Exception as e:
        error_msg = f"Error calling current war API for {clan_tag}: {e}\n"
        error_msg += f"{traceback.format_exc()}"
        current_app.logger.error(error_msg)
        flash("An unexpected error occcurred while fetching current war data. Please try again later.", 'danger')
        war_data = None
    
    dumpdata = json.dumps(clan_war_team, indent=4).replace("\n", "<br>")    
    return render_template('currentwar.html', ThisHTML="currentwar", ClanWar=war_data, 
                           ClanWarTeam=clan_war_team, dumpdata=dumpdata, 
                           cocparm=current_app.cocinfo_cocparm)

@clan_bp.route('/clan/warlog/<clan_tag>', methods=['GET'])
def display_war_log(clan_tag: str):
    war_log_data = current_app.coc_api_client.get_clan_war_log(clan_tag)
    if war_log_data and 'error' in war_log_data:
        flash(f"Error fetching war log data: {war_log_data['error']}", 'danger')
        war_log_data = None
    elif not war_log_data:
        flash(f"No war log data for tag: {clan_tag}.", 'warning')
    else:
        war_log_data['clan'] = {}
        war_log_data['player'] = {}
        for war_log in war_log_data['print']:
            war_log_endTime = war_log['endTime'][:8]
            if war_log_data['warlog'][war_log_endTime]['state'] != 'noData':
                for member in war_log_data['warlog'][war_log_endTime]['clan']['members']:
                    if member['tag'] not in war_log_data['clan']:
                        war_log_data['clan'][member['tag']] = copy.deepcopy(member)
                        war_log_data['player'][member['tag']] = copy.deepcopy(member)
                        war_log_data['clan'][member['tag']]['mapPositionSum'] = member['mapPosition']
                        war_log_data['clan'][member['tag']]['mapPositionCount'] = 1
                    else:
                        war_log_data['clan'][member['tag']]['mapPositionSum'] += member['mapPosition']
                        war_log_data['clan'][member['tag']]['mapPositionCount'] += 1
                    if 'attacks' in member:
                        war_log_data['clan'][member['tag']][war_log_endTime + '-1'] = copy.deepcopy(member['attacks'][0])
                        if len(member['attacks']) > 1:
                            war_log_data['clan'][member['tag']][war_log_endTime + '-2'] = copy.deepcopy(member['attacks'][1])
                        else:
                            war_log_data['clan'][member['tag']][war_log_endTime + '-2'] = {}
                    else:
                        war_log_data['clan'][member['tag']][war_log_endTime + '-1'] = {}
                        war_log_data['clan'][member['tag']][war_log_endTime + '-2'] = {}
                for member in war_log_data['warlog'][war_log_endTime]['opponent']['members']:
                    war_log_data['player'][member['tag']] = copy.deepcopy(member)
        war_log_data['mapPositionSeq'] = {}
        for membertag in war_log_data['clan']:
            war_log_data['clan'][membertag]['mapPositionAvg'] = \
                war_log_data['clan'][membertag]['mapPositionSum'] / war_log_data['clan'][membertag]['mapPositionCount']
            war_log_data['mapPositionSeq']["{:04.1f}".format(war_log_data['clan'][membertag]['mapPositionAvg']) + membertag] = membertag
        war_log_data['mapPositionSeq'] = dict(sorted(war_log_data['mapPositionSeq'].items()))
        # fetch other member data into summary table
        clan_data = current_app.coc_api_client.get_clan_details(clan_tag)
        for member in clan_data['memberList']:
            if member['tag'] not in war_log_data['clan']:
                war_log_data['mapPositionSeq']['99.9' + member['tag']] = member['tag']
                war_log_data['clan'][member['tag']] = {'mapPositionAvg' : 99.9}
                war_log_data['clan'][member['tag']]['townhallLevel'] = member['townHallLevel']
                war_log_data['clan'][member['tag']]['name'] = member['name']
    dumpdata = json.dumps(war_log_data, indent=4).replace("\n", "<br>").replace(" ", "&nbsp;")   
    return render_template('clanwarlog.html', ThisHTML="clanwarlog", ClanWarLog=war_log_data, 
                           cocparm=current_app.cocinfo_cocparm,
                           dumpdata=dumpdata)




@clan_bp.route('/wardetail/<clan_tag>/<war_date>', methods=['GET'])
def display_wardetail(clan_tag: str, war_date: str):
    clan_war_team = {
            'clan': {},
            'opponent': {},
            'player': {},
            'order': {}
        }

    war_data = current_app.coc_api_client.get_war_detail(clan_tag, war_date)
    if war_data and war_data['state'] != 'noData':
        for group in ['clan', 'opponent']:
            for member in war_data[group]['members']:
                clan_war_team[group][member['mapPosition']] = copy.deepcopy(member)
                clan_war_team['player'][member['tag']] = copy.deepcopy(member)
                if 'attacks' in member:
                    for attack in member['attacks']:
                        if 'order' in attack:
                            clan_war_team['order'][attack['order']] = copy.deepcopy(attack)
                            clan_war_team['order'][attack['order']]['team'] = group
        clan_war_team['orderSeq'] = sorted(clan_war_team['order'].keys())
    else:
        flash(f"No war data of {clan_tag} on {war_date}")
        war_data = None

    dumpdata = json.dumps(clan_war_team, indent=4).replace("\n", "<br>").replace(" ", "&nbsp;")
    return render_template('currentwar.html', ThisHTML="currentwar", ClanWar=war_data, 
                           ClanWarTeam=clan_war_team, dumpdata=dumpdata,
                           cocparm=current_app.cocinfo_cocparm)





