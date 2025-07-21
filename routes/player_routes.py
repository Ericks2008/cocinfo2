# ./routes/player_routes.py

from flask import Blueprint, render_template, request, current_app, flash
import urllib.parse
import copy
import cocparm # Assuming cocparm is accessible or passed

from flask_wtf import FlaskForm
from wtforms.fields import DateField
from wtforms.validators import DataRequired
from wtforms import validators, SubmitField

player_bp = Blueprint('player_bp', __name__)


class InfoForm(FlaskForm):
    playerdate = DateField('End Date', format='%Y-%m-%d', validators=(validators.DataRequired(),))
    submit = SubmitField('End Date')


@player_bp.route('/player/<string:player_tag>/info', methods=['GET'])
def display_player_info(player_tag):
    # get_player_info() replace player()
    PlayerMetric = ['warStars', 'attackWins', 'donations', 'donationsReceived']
    from_date = request.args.get('playerdate')
    player_data = None
    form = InfoForm()
    try:
        if from_date:
            player_data = current_app.coc_api_client.get_player_info(player_tag, from_date)
        else:
            player_data = current_app.coc_api_client.get_player_info(player_tag)
        if player_data and 'error' in player_data:
            flash(f"Error fetching player data: {player_data['error']}", 'danger')
            player_data = None # Ensure PlayerData is None for the template to show error state
        elif not player_data: # If API call returns None for some reason
            flash(f"Could not retrieve data for player tag: {player_tag}.", 'warning')
    except Exception as e: # Catch network errors or issues with coc_api_client itself
        current_app.logger.error(f"Error calling player API for {player_tag}: {e}")
        flash("An unexpected error occurred while fetching player data. Please try again later.", 'danger')
        player_data = None # Ensure PlayerData is None

    return render_template('player_info.html', ThisHTML="player", PlayerData=player_data, 
                           PlayerMetric=PlayerMetric, form=form)

@player_bp.route('/player/<string:player_tag>/upgrade/progress', methods=['GET'])
def display_player_progress(player_tag):
    player_data = None # Initialize
    try:
        player_data = current_app.coc_api_client.get_player_progress(player_tag)
        if player_data and 'error' in player_data:
            flash(f"Error fetching player upgrade data: {player_data['error']}", 'danger')
            player_data = None
        elif not player_data:
            flash(f"Could not retrieve upgrade data for player tag: {player_tag}.", 'warning')
    except Exception as e:
        current_app.logger.error(f"Error calling player upgrade progress API for {player_tag}: {e}")
        flash("An unexpected error occurred while fetching player upgrade data. Please try again later.", 'danger')
        player_data = None

    return render_template('playerprogress.html', ThisHTML="player", PlayerData=player_data)



