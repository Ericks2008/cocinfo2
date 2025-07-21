# ./api_client/coc_api_service.py
import urllib.request
import json
import logging
import copy # Used for deepcopy in original functions

class CocApiClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__) # Use the app-wide logger if desired, or a dedicated one

    def _make_request(self, endpoint, params=None, method='GET', json_data=None):
        """
        Generic helper to make requests to the COC data service.
        Handles URL construction, headers, JSON encoding/decoding, and basic error logging.
        """
        url = f"{self.base_url}/{endpoint}"
        self.logger.warning(url)
        if params:
            encoded_params = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            if encoded_params:
                url += "?" + encoded_params

        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/json')
        
        request_body = None
        if json_data:
            req.add_header('Content-Type', 'application/json; charset=utf-8')
            request_body = json.dumps(json_data).encode('utf-8')
            req.add_header('Content-Length', len(request_body))
            req.get_method = lambda: method # For POST/PUT with urllib

        try:
            with urllib.request.urlopen(req, request_body) as r:
                resp = r.read()
                return json.loads(resp)
        except urllib.error.URLError as e:
            self.logger.error(f"URLError when calling {url}: {e.reason} (Code: {e.code if hasattr(e, 'code') else 'N/A'})")
            # You might want to raise a custom exception here or return None/empty dict
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSONDecodeError for {url}: {e.msg}. Response: {resp.decode('utf-8')[:200]}...")
            return None
        except Exception as e:
            self.logger.exception(f"Unexpected error during API call to {url}")
            return None

    # --- API Specific Methods (Encapsulating original read_from_coc calls) ---
    def get_cwl_list(self, clan_tag):
        return self._make_request('api/cwl/get_cwl_list/' + urllib.parse.quote(clan_tag))

    def get_clan_details(self, clan_tag):
        return self._make_request('api/clan/get_clan_details/' + urllib.parse.quote(clan_tag))

    def get_player_info(self, player_tag, from_date=None):
        get_player_info_url = 'api/player/get_player_info/' + urllib.parse.quote(player_tag)
        if from_date:
            get_player_info_url += '/' + urllib.parse.quote(from_date)
        return self._make_request(get_player_info_url)

    def get_player_progress(self, player_tag):
        return self._make_request('api/player/get_player_progress_data/' + urllib.parse.quote(player_tag))

    def get_clan_supertroops(self, clan_tag):
        return self._make_request('api/clan/supertroops/' + urllib.parse.quote(clan_tag))

    def get_clan_troops(self, clan_tag):
        return self._make_request("api/clan/troops/" + urllib.parse.quote(clan_tag))

    def get_clan_progress(self, clan_tag, achievement):
        get_clan_progress_url = 'api/clan/progress/' + urllib.parse.quote(clan_tag)
        if achievement:
            get_clan_progress_url += '/' + urllib.parse.quote(achievement)
        return self._make_request(get_clan_progress_url)

    def get_cwl_info(self, clan_tag, season=None):
        get_cwl_info_url = 'api/cwl/get_cwl_season_data/' + urllib.parse.quote(clan_tag)
        if season:
            get_cwl_info_url += '/' + urllib.parse.quote(season)
        return self._make_request(get_cwl_info_url)

    def get_war_tag_detail(self, war_tag, season):
        return self._make_request('api/cwl/wartag/' + urllib.parse.quote(war_tag) + '/' + urllib.parse.quote(season))

    def get_cwl_summary(self, clan_tag, season):
        get_cwl_summary_sql = 'api/cwl/summary/' + urllib.parse.quote(clan_tag)
        if season:
            get_cwl_summary_sql += '/' + urllib.parse.quote(season)
        return self._make_request(get_cwl_summary_sql)

    def get_current_war(self, clan_tag):
        return self._make_request('api/clan/currentwar/' + urllib.parse.quote(clan_tag))

    def get_clan_war_log(self, clan_tag):
        return self._make_request('api/clan/warlog/' + urllib.parse.quote(clan_tag))


    def get_war_detail(self, clan_tag, war_date):
        return self._make_request('api/clan/wardetail/' + urllib.parse.quote(clan_tag) + '/' + urllib.parse.quote(war_date))


    # --

    # You could also add caching logic here within these methods or in _make_request.
