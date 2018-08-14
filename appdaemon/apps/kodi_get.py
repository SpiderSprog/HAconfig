import appdaemon.plugins.hass.hassapi as hass

EVENT_KODI_CALL_METHOD_RESULT = 'kodi_call_method_result'

ENTITY = 'input_select.kodi_results'
MEDIA_PLAYER = 'media_player.kodi'
DEFAULT_ACTION = "Nothing to do"
MAX_RESULTS = 20

class DynamicKodiInputSelect(hass.Hass):
    """AppDaemon app to dynamically populate an `input_select`."""
    _ids_options = None

    def initialize(self):
        """Set up appdaemon app."""
        self.listen_event(self._receive_kodi_result,
                          EVENT_KODI_CALL_METHOD_RESULT)
        self.listen_state(self._change_selected_option, ENTITY)
        # Input select:
        self._ids_options = {DEFAULT_ACTION: None}

    def _receive_kodi_result(self, event_id, payload_event, *args):
        result = payload_event['result']
        method = payload_event['input']['method']

        assert event_id == EVENT_KODI_CALL_METHOD_RESULT
        if method == 'VideoLibrary.GetRecentlyAddedMovies':
            values = result['movies'][:MAX_RESULTS]
            data = [('{} ({})'.format(r['label'], r['year']),
                     ('MOVIE', r['file'])) for r in values]
            self._ids_options.update(dict(zip(*zip(*data))))
            labels = list(list(zip(*data))[0])
            self.call_service('input_select/set_options',
                              entity_id=ENTITY,
                              options=[DEFAULT_ACTION] + labels)
            self.set_state(ENTITY,
                           attributes={"friendly_name": 'Recent Movies',
                                       "icon": 'mdi:movie'})
        elif method == 'VideoLibrary.GetRecentlyAddedEpisodes':
            values = list(filter(lambda r: not r['lastplayed'],
                                 result['episodes']))[:MAX_RESULTS]
            data = [('{} - {}'.format(r['showtitle'], r['label']),
                     ('TVSHOW', r['file'])) for r in values]
            self._ids_options.update(dict(zip(*zip(*data))))
            labels = list(list(zip(*data))[0])
            self.call_service('input_select/set_options',
                              entity_id=ENTITY,
                              options=[DEFAULT_ACTION] + labels)
            self.set_state(ENTITY,
                           attributes={"friendly_name": 'Recent TvShows',
                                       "icon": 'mdi:play-circle'})
        elif method == 'PVR.GetChannels':
            values = result['channels']
            data = [(r['label'], ('CHANNEL', r['channelid']))
                    for r in values]
            self._ids_options.update(dict(zip(*zip(*data))))
            labels = list(list(zip(*data))[0])
            self.call_service('input_select/set_options',
                              entity_id=ENTITY,
                              options=[DEFAULT_ACTION] + labels)
            self.set_state(ENTITY,
                           attributes={"friendly_name": 'TV channels',
                                       "icon": 'mdi:play-box-outline'})

    def _change_selected_option(self, entity, attribute, old, new, kwargs):
        selected = self._ids_options[new]
        if selected:
            mediatype, file = selected
            self.call_service('media_player/play_media',
                              entity_id=MEDIA_PLAYER,
                              media_content_type=mediatype,
                              media_content_id=file)