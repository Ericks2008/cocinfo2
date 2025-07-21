
import datetime
import urllib.request
import json
import copy
import cocparm
from datetime import datetime
from utils.logger_config import setup_logging
from utils.get_secret import get_secret_from_secret_manager_auto
from utils.helper import get_level_badge_class

from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms.fields import DateField
from wtforms.validators import DataRequired
from wtforms import validators, SubmitField

# Import API Client
from api_client.coc_api_service import CocApiClient

# Import Blueprints
from routes.clan_routes import clan_bp
from routes.player_routes import player_bp
from routes.cwl_routes import cwl_bp

app_logger = setup_logging()

app = Flask(__name__)
app.app_logger = app_logger

# Load secrets
app.secret_key = get_secret_from_secret_manager_auto('app_secret_key')
coc_data_service_url = get_secret_from_secret_manager_auto('coc_data_service_url')

# Initialize API Client (make it available globally or pass to blueprints)
# A more robust solution might use Flask's application context or extensions
app.coc_api_client = CocApiClient(coc_data_service_url)

# Register Blueprints
app.register_blueprint(clan_bp)
app.register_blueprint(player_bp)
app.register_blueprint(cwl_bp)

#class InfoForm(FlaskForm):
#    playerdate = DateField('End Date', format='%Y-%m-%d', validators=(validators.DataRequired(),))
#    submit = SubmitField('End Date')

@app.template_filter('format_coc_time')
def format_coc_time_filter(iso_string):
    try:
        # COC API returns 'YYYYMMDDTHHMMSS.000Z'
        dt_object = datetime.strptime(iso_string.split('.')[0], '%Y%m%dT%H%M%S')
        return dt_object.strftime('%d/%m/%Y %H:%M')
    except (ValueError, TypeError):
        return 'N/A'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
