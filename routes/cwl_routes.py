# ./routes/cwl_routes.py
from flask import Blueprint, render_template, request, current_app, flash
import urllib.parse
import json
import copy
import cocparm # Assuming cocparm is accessible or passed
from utils.helper import get_level_badge_class

cwl_bp = Blueprint('cwl_bp', __name__)

@cwl_bp.route('/cwlinfo/<clan_tag>', defaults={'season': None}, methods=['GET'])
@cwl_bp.route('/cwlinfo/<clan_tag>/<season>', methods=['GET'])
def display_cwl_info(clan_tag, season:None):
    cwl_data = None
    try:
        cwl_data = current_app.coc_api_client.get_cwl_info(clan_tag, season)
        if cwl_data and 'error' in cwl_data:
            flash(f"Error fetching cwl data: {cwl_data['error']}", 'danger')
            cwl_data = None
        elif not cwl_data:
            flash(f"Could not retrieve cwl data for clan: {clan_tag}.", 'warning')
    except Exception as e:
        current_app.logger.error(f"Error calling cwl info API for {clan_tag}: {e}")
        flash("An unexpected error occurred while fetching cwl data. Please try again later.", 'danger')
        cwl_data = None
    if cwl_data:
        for clan in cwl_data['clans']:
            consolidated_data = {}
            consolidated_member_count = {}
            for member in clan['members']:
                level = member['townHallLevel']
                if level not in consolidated_data:
                    consolidated_data[level] = []
                    consolidated_member_count[level] = 0
                consolidated_data[level].append(member)
                consolidated_member_count[level] = consolidated_member_count[level] + 1
            clan['consolidated_member'] = {k: v for k, v in sorted(consolidated_data.items(), key=lambda item:item[0], reverse=True)}
            clan['consolidated_member_count'] = consolidated_member_count
        round = 1
        for round_detail in cwl_data['rounds']:
            round_detail['day'] = round
            round = round + 1
    return render_template('clanwarleague.html', ThisHTML="clanwarleague", ClanWar=cwl_data)



@cwl_bp.route('/wartag/<clan_tag>/<season>/<round_day>', methods=['GET'])
def wartag(clan_tag, season, round_day):
    cwl_data = current_app.coc_api_client.get_cwl_info(clan_tag, season)
    if cwl_data and 'error' in cwl_data:
        flash(f"Error fetching cwl data: {cwl_data['error']}", 'danger')
        cwl_data = None
    elif not cwl_data:
        flash(f"Could not retrieve cwl data for clan: {clan_tag}.", 'warning')

    round_index = int(round_day) - 1
    total_member_list = {}
    dumpdata = None
    if cwl_data:
        if 'rounds' in cwl_data and len(cwl_data['rounds']) > round_index:
            target_round_data = cwl_data['rounds'][round_index]
            for war_tag in target_round_data.get('warTags', []):
                if war_tag == '#0':
                    target_round_data[war_tag] = None
                    continue
                target_round_data[war_tag] = current_app.coc_api_client.get_war_tag_detail(war_tag[1:], season)
                # sort clan member in mapPosition order
                if (target_round_data[war_tag].get('clan') and 
                    target_round_data[war_tag]['clan'].get('members')):
                    members_list = target_round_data[war_tag]['clan']['members']
                    for member in members_list:
                        total_member_list[member['tag']] = member
                    members_list.sort(key=lambda member_dict: int(member_dict['mapPosition']))
                # sort oppopent member in mapPosition order
                if (target_round_data[war_tag].get('opponent') and 
                    target_round_data[war_tag]['opponent'].get('members')):
                    members_list = target_round_data[war_tag]['opponent']['members']
                    for member in members_list:
                        total_member_list[member['tag']] = member
                    members_list.sort(key=lambda member_dict: int(member_dict['mapPosition']))

                war_tag_data = cwl_data['rounds'][round_index][war_tag]
                if (war_tag_data['clan']['stars'] > war_tag_data['opponent']['stars'] or
                    (war_tag_data['clan']['stars'] == war_tag_data['opponent']['stars'] and 
                     war_tag_data['clan']['destructionPercentage'] > war_tag_data['opponent']['destructionPercentage'])):
                    war_tag_data['result'] = 'win'
                else:
                    war_tag_data['result'] = 'lost'
        dumpdata = json.dumps(cwl_data, indent=4).replace("\n", "<br>").replace(" ", "&nbsp;")   
    return render_template('wartag.html', ThisHTML='clanwarleague', ClanWar=cwl_data, RoundDay=round_index, 
                           totalMemberList=total_member_list, dumpdata=dumpdata)

@cwl_bp.route('/cwlsummary/<clan_tag>/<season>', methods=['GET'])
def cwlsummary(clan_tag: str, season: str):
    
    cwl_summary_data = current_app.coc_api_client.get_cwl_summary(clan_tag, season)
    if 'rounds' in cwl_summary_data:
        clanlist = cwl_summary_data['clanlist']
        clansummary = cwl_summary_data['clansummary']
        dumpdata = json.dumps(clanlist, indent=4).replace("\n", "<br>").replace(" ", "&nbsp;")    
        return render_template('cwlteam.html', ThisHTML="clanwarleague", ClanWar=cwl_summary_data, 
                               clanlist=clanlist, clansummary=clansummary, dumpdata=dumpdata)
    else:
        flash(f"Error fetching CWL summary for clan {clan_tag}, season {season}: {cwl_summary_data.get('error', 'Unknown error')}", 'danger')
        return render_template('cwlteam.html', ThisHTML="clanwarleague", ClanWar=None, clanlist=None, clansummary=None)





