# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""

from mock import patch, PropertyMock
import os
import tempfile
import textwrap
import json
from webob import Request

from xmodule.contentstore.content import StaticContent
from xmodule.modulestore import Location
from xmodule.contentstore.django import contentstore
from . import BaseTestXmodule
from .test_video_xml import SOURCE_XML
from django.conf import settings
from xmodule.video_module import create_youtube_string
from cache_toolbox.core import del_cached_content
from xmodule.exceptions import NotFoundError

class TestVideo(BaseTestXmodule):
    """Integration tests: web client + mongo."""
    CATEGORY = "video"
    DATA = SOURCE_XML
    METADATA = {}

    def test_handle_ajax_dispatch(self):
        responses = {
            user.username: self.clients[user.username].post(
                self.get_url('whatever'),
                {},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            for user in self.users
        }

        self.assertEqual(
            set([
                response.status_code
                for _, response in responses.items()
                ]).pop(),
            404)

    def tearDown(self):
        _clear_assets(self.item_descriptor.location)


class TestVideoYouTube(TestVideo):
    METADATA = {}

    def test_video_constructor(self):
        """Make sure that all parameters extracted correctly from xml"""
        context = self.item_descriptor.render('student_view').content

        sources = {
            'main': u'example.mp4',
            u'mp4': u'example.mp4',
            u'webm': u'example.webm',
        }

        expected_context = {
            'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', False),
            'data_dir': getattr(self, 'data_dir', None),
            'display_name': u'A Name',
            'end': 3610.0,
            'id': self.item_descriptor.location.html_id(),
            'show_captions': 'true',
            'sources': sources,
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'saved_video_position': 0.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': None,
            'youtube_streams': create_youtube_string(self.item_descriptor),
            'yt_test_timeout': 1500,
            'yt_test_url': 'https://gdata.youtube.com/feeds/api/videos/',
            'transcript_language': 'en',
            'transcript_languages' : '{"uk": "Ukrainian", "en": "English"}',
            'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript'
            ).rstrip('/?') + '/translation',
        }
        self.assertEqual(
            context,
            self.item_descriptor.xmodule_runtime.render_template('video.html', expected_context),
        )


class TestVideoNonYouTube(TestVideo):
    """Integration tests: web client + mongo."""
    DATA = """
        <video show_captions="true"
        display_name="A Name"
        sub="a_sub_file.srt.sjson"
        download_video="true"
        start_time="01:00:03" end_time="01:00:10"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
        </video>
    """
    MODEL_DATA = {
        'data': DATA,
    }
    METADATA = {}

    def test_video_constructor(self):
        """Make sure that if the 'youtube' attribute is omitted in XML, then
            the template generates an empty string for the YouTube streams.
        """
        sources = {
            'main': u'example.mp4',
            u'mp4': u'example.mp4',
            u'webm': u'example.webm',
        }

        context = self.item_descriptor.render('student_view').content
        expected_context = {
            'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
            'data_dir': getattr(self, 'data_dir', None),
            'show_captions': 'true',
            'display_name': u'A Name',
            'end': 3610.0,
            'id': self.item_descriptor.location.html_id(),
            'sources': sources,
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'saved_video_position': 0.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': None,
            'youtube_streams': '1.00:OEoXaMPEzfM',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_test_url': 'https://gdata.youtube.com/feeds/api/videos/',
            'transcript_language': 'en',
            'transcript_languages' : '{"en": "English"}',
            'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript'
            ).rstrip('/?') + '/translation',
        }

        self.assertEqual(
            context,
            self.item_descriptor.xmodule_runtime.render_template('video.html', expected_context),
        )


class TestGetHtmlMethod(BaseTestXmodule):
    '''
    Make sure that `get_html` works correctly.
    '''
    CATEGORY = "video"
    DATA = SOURCE_XML
    METADATA = {}

    def setUp(self):
        self.setup_course();

    def test_get_html_track(self):
        SOURCE_XML = """
            <video show_captions="true"
            display_name="A Name"
                sub="{sub}" download_track="{download_track}"
            start_time="01:00:03" end_time="01:00:10"
            >
                <source src="example.mp4"/>
                <source src="example.webm"/>
                {track}
            </video>
        """

        cases = [
            {
                'download_track': u'true',
                'track': u'<track src="http://www.example.com/track"/>',
                'sub': u'a_sub_file.srt.sjson',
                'expected_track_url': u'http://www.example.com/track',
            },
            {
                'download_track': u'true',
                'track': u'',
                'sub': u'a_sub_file.srt.sjson',
                'expected_track_url': u'a_sub_file.srt.sjson',
            },
            {
                'download_track': u'true',
                'track': u'',
                'sub': u'',
                'expected_track_url': None
            },
            {
                'download_track': u'false',
                'track': u'<track src="http://www.example.com/track"/>',
                'sub': u'a_sub_file.srt.sjson',
                'expected_track_url': None,
            },
        ]

        expected_context = {
            'data_dir': getattr(self, 'data_dir', None),
            'show_captions': 'true',
            'display_name': u'A Name',
            'end': 3610.0,
            'id': None,
            'sources': {
                'main': u'example.mp4',
                u'mp4': u'example.mp4',
                u'webm': u'example.webm'
            },
            'start': 3603.0,
            'saved_video_position': 0.0,
            'sub': u'a_sub_file.srt.sjson',
            'speed': 'null',
            'general_speed': 1.0,
            'track': u'http://www.example.com/track',
            'youtube_streams': '1.00:OEoXaMPEzfM',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_test_url': 'https://gdata.youtube.com/feeds/api/videos/',
        }

        for data in cases:
            DATA = SOURCE_XML.format(
                download_track=data['download_track'],
                track=data['track'],
                sub=data['sub']
            )

            self.initialize_module(data=DATA)
            track_url = self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript'
            ).rstrip('/?') + '/download'

            context = self.item_descriptor.render('student_view').content

            expected_context.update({
                'transcript_languages' : '{"en": "English"}' if self.item_descriptor.sub else '{}',
                'transcript_language': 'en' if self.item_descriptor.sub else json.dumps(None),
                'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                    self.item_descriptor, 'transcript'
                ).rstrip('/?') + '/translation',
                'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
                'track': track_url if data['expected_track_url'] == u'a_sub_file.srt.sjson' else data['expected_track_url'],
                'sub': data['sub'],
                'id': self.item_descriptor.location.html_id(),
            })

            self.assertEqual(
                context,
                self.item_descriptor.xmodule_runtime.render_template('video.html', expected_context),
            )

    def test_get_html_source(self):
        SOURCE_XML = """
            <video show_captions="true"
            display_name="A Name"
            sub="a_sub_file.srt.sjson" source="{source}"
            download_video="{download_video}"
            start_time="01:00:03" end_time="01:00:10"
            >
                {sources}
            </video>
        """
        cases = [
            # self.download_video == True
            {
                'download_video': 'true',
                'source': 'example_source.mp4',
                'sources': """
                    <source src="example.mp4"/>
                    <source src="example.webm"/>
                """,
                'result': {
                    'main': u'example_source.mp4',
                    u'mp4': u'example.mp4',
                    u'webm': u'example.webm',
                },
            },
            {
                'download_video': 'true',
                'source': '',
                'sources': """
                    <source src="example.mp4"/>
                    <source src="example.webm"/>
                """,
                'result': {
                    'main': u'example.mp4',
                    u'mp4': u'example.mp4',
                    u'webm': u'example.webm',
                },
            },
            {
                'download_video': 'true',
                'source': '',
                'sources': [],
                'result': {},
            },

            # self.download_video == False
            {
                'download_video': 'false',
                'source': 'example_source.mp4',
                'sources': """
                    <source src="example.mp4"/>
                    <source src="example.webm"/>
                """,
                'result': {
                    u'mp4': u'example.mp4',
                    u'webm': u'example.webm',
                },
            },
        ]

        expected_context = {
            'data_dir': getattr(self, 'data_dir', None),
            'show_captions': 'true',
            'display_name': u'A Name',
            'end': 3610.0,
            'id': None,
            'sources': None,
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'saved_video_position': 0.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': None,
            'youtube_streams': '1.00:OEoXaMPEzfM',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_test_url': 'https://gdata.youtube.com/feeds/api/videos/',
            'transcript_language': 'en',
            'transcript_languages' : '{"en": "English"}',
        }

        for data in cases:
            DATA = SOURCE_XML.format(
                download_video=data['download_video'],
                source=data['source'],
                sources=data['sources']
            )
            self.initialize_module(data=DATA)
            context = self.item_descriptor.render('student_view').content

            expected_context.update({
                'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                    self.item_descriptor, 'transcript'
                ).rstrip('/?') + '/translation',
                'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
                'sources': data['result'],
                'id': self.item_descriptor.location.html_id(),
            })

            self.assertEqual(
                context,
                self.item_descriptor.xmodule_runtime.render_template('video.html', expected_context)
            )


class TestVideoDescriptorInitialization(BaseTestXmodule):
    """
    Make sure that module initialization works correctly.
    """
    CATEGORY = "video"
    DATA = SOURCE_XML
    METADATA = {}

    def setUp(self):
        self.setup_course();

    def test_source_not_in_html5sources(self):
        metadata = {
            'source': 'http://example.org/video.mp4',
            'html5_sources': ['http://youtu.be/OEoXaMPEzfM.mp4'],
        }

        self.initialize_module(metadata=metadata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertIn('source', fields)
        self.assertEqual(self.item_descriptor.source, 'http://example.org/video.mp4')
        self.assertTrue(self.item_descriptor.download_video)
        self.assertTrue(self.item_descriptor.source_visible)

    def test_source_in_html5sources(self):
        metadata = {
            'source': 'http://example.org/video.mp4',
            'html5_sources': ['http://example.org/video.mp4'],
        }

        self.initialize_module(metadata=metadata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertNotIn('source', fields)
        self.assertTrue(self.item_descriptor.download_video)
        self.assertFalse(self.item_descriptor.source_visible)

    @patch('xmodule.video_module.VideoDescriptor.editable_metadata_fields', new_callable=PropertyMock)
    def test_download_video_is_explicitly_set(self, mock_editable_fields):
        mock_editable_fields.return_value = {
            'download_video': {
                'default_value': False,
                'explicitly_set': True,
                'display_name': 'Video Download Allowed',
                'help': 'Show a link beneath the video to allow students to download the video.',
                'type': 'Boolean',
                'value': False,
                'field_name': 'download_video',
                'options': [
                    {'display_name': "True", "value": True},
                    {'display_name': "False", "value": False}
                ],
            },
            'html5_sources': {
                'default_value': [],
                'explicitly_set': False,
                'display_name': 'Video Sources',
                'help': 'A list of filenames to be used with HTML5 video.',
                'type': 'List',
                'value': [u'http://youtu.be/OEoXaMPEzfM.mp4'],
                'field_name': 'html5_sources',
                'options': [],
            },
            'source': {
                'default_value': '',
                'explicitly_set': False,
                'display_name': 'Download Video',
                'help': 'The external URL to download the video.',
                'type': 'Generic',
                'value': u'http://example.org/video.mp4',
                'field_name': 'source',
                'options': [],
            },
            'track': {
                'default_value': '',
                'explicitly_set': False,
                'display_name': 'Download Transcript',
                'help': 'The external URL to download the timed transcript track.',
                'type': 'Generic',
                'value': u'',
                'field_name': 'track',
                'options': [],
            },
            'transcripts': {
                # purely mocked
            }
        }
        metadata = {
            'track': None,
            'source': 'http://example.org/video.mp4',
            'html5_sources': ['http://youtu.be/OEoXaMPEzfM.mp4'],
        }

        self.initialize_module(metadata=metadata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertIn('source', fields)
        self.assertFalse(self.item_descriptor.download_video)
        self.assertTrue(self.item_descriptor.source_visible)

    def test_source_is_empty(self):
        metadata = {
            'source': '',
            'html5_sources': ['http://youtu.be/OEoXaMPEzfM.mp4'],
        }

        self.initialize_module(metadata=metadata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertNotIn('source', fields)
        self.assertFalse(self.item_descriptor.download_video)


def _create_srt_file(content=None, lang='uk'):
    """
    Create srt file in filesystem.
    """
    content = content or textwrap.dedent("""
        0
        00:00:00,12 --> 00:00:00,100
        Привіт, edX вітає вас.
    """)
    srt_file = tempfile.NamedTemporaryFile(suffix=".srt")
    srt_file.content_type = 'application/x-subrip'
    srt_file.write(content)
    srt_file.seek(0)
    return srt_file


class TestVideoHandlers(TestVideo):

    non_en_file = _create_srt_file()
    DATA = """
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
            <transcript language="uk" src="{}"/>
        </video>
    """.format(os.path.split(non_en_file.name)[1])

    MODEL_DATA = {
        'data': DATA
    }

    def test_language_is_not_supported(self):
        request = Request.blank('/download?language=ru')
        response = self.item_descriptor.transcript(request=request, dispatch='download')
        self.assertEqual(response.status, '404 Not Found')

    def test_download_transcript_not_exist(self):
        request = Request.blank('/download?language=en')
        response = self.item_descriptor.transcript(request=request, dispatch='download')
        self.assertEqual(response.status, '404 Not Found')

    @patch('xmodule.video_module.VideoModule.get_transcript', return_value='Subs!')
    def test_download_exist(self, __):
        request = Request.blank('/download?language=en')
        response = self.item_descriptor.transcript(request=request, dispatch='download')
        self.assertEqual(response.body, 'Subs!')

    def test_translation_fails(self):
        # no videoId
        request = Request.blank('/translation?language=ru')
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        self.assertEqual(response.status, '400 Bad Request')

        # videoId not found
        request = Request.blank('/translation?language=ru&videoId=12345')
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        self.assertEqual(response.status, '404 Not Found')

        #language is 'en' but self.sub is None
        request = Request.blank('/translation?language=en&videoId=12345')
        # to get instance
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance
        item.sub = ""
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        self.assertEqual(response.status, '404 Not Found')

    def test_translaton_en_success(self):
        subs = {"start": [10,], "end": [100,], "text": [ "Hi, welcome to Edx.",]}
        good_sjson = _create_file(json.dumps(subs))
        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        subs_id = _get_subs_id(good_sjson.name)

        # to get instance
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        item.sub = subs_id
        request = Request.blank('/translation?language=en&videoId={}'.format(subs_id))
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        self.assertDictEqual(json.loads(response.body), subs)

    def test_translaton_non_en_non_youtube_success(self):
        subs =  {
            u'end': [100],
            u'start': [12],
            u'text': [
            u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
        ]}
        self.non_en_file.seek(0)
        _upload_file(self.non_en_file, self.item_descriptor.location, os.path.split(self.non_en_file.name)[1])
        subs_id = _get_subs_id(self.non_en_file.name)

        # to get instance
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance
        # manually clean youtube_id_1_0, as it has default value
        item.youtube_id_1_0 = ""

        request = Request.blank('/translation?language=uk&videoId={}'.format(subs_id))
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        self.assertDictEqual(json.loads(response.body), subs)

    def test_translation_non_en_youtube(self):
        subs =  {
            u'end': [100],
            u'start': [12],
            u'text': [
            u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
        ]}
        self.non_en_file.seek(0)
        _upload_file(self.non_en_file, self.item_descriptor.location, os.path.split(self.non_en_file.name)[1])
        subs_id = _get_subs_id(self.non_en_file.name)
        # to get instance

        # youtube 1_0 request, will generate for all speeds for existing ids
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance
        item.youtube_id_1_0 = subs_id
        item.youtube_id_0_75 = '0_75'
        request = Request.blank('/translation?language=uk&videoId={}'.format(subs_id))
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        self.assertDictEqual(json.loads(response.body), subs)

        # 0_75 subs are exist
        request = Request.blank('/translation?language=uk&videoId={}'.format('0_75'))
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        calculated_0_75 = {
            u'end': [75],
            u'start': [9],
            u'text': [
            u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
        ]}
        self.assertDictEqual(json.loads(response.body), calculated_0_75)
        # 1_5 will be generated from 1_0
        item = self.item_descriptor.xmodule_runtime.xmodule_instance
        item.youtube_id_1_5 = '1_5'
        request = Request.blank('/translation?language=uk&videoId={}'.format('1_5'))
        response = self.item_descriptor.transcript(request=request, dispatch='translation')
        calculated_1_5 = {
            u'end': [150],
            u'start': [18],
            u'text': [
            u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
        ]}
        self.assertDictEqual(json.loads(response.body), calculated_1_5)


class TestVideoGetTranscriptsMethod(TestVideo):
    """
    Make sure that `get_transcript` method works correctly
    """

    DATA = """
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
        </video>
    """
    MODEL_DATA = {
        'data': DATA
    }
    METADATA = {}

    def test_good_transcript(self):
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        good_sjson = _create_file(content=textwrap.dedent("""\
                {
                  "start": [
                    270,
                    2720
                  ],
                  "end": [
                    2720,
                    5430
                  ],
                  "text": [
                    "Hi, welcome to Edx.",
                    "Let&#39;s start with what is on your screen right now."
                  ]
                }
            """))

        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        item.sub = _get_subs_id(good_sjson.name)
        text = item.get_transcript('en')
        expected_text = textwrap.dedent("""\
            0
            00:00:00,270 --> 00:00:02,720
            Hi, welcome to Edx.

            1
            00:00:02,720 --> 00:00:05,430
            Let&#39;s start with what is on your screen right now.

            """)

        self.assertEqual(text, expected_text)

    def test_not_found_error(self):
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        with self.assertRaises(NotFoundError):
            item.get_transcript('en')

    def test_value_error(self):
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        good_sjson = _create_file(content='bad content')

        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        item.sub = _get_subs_id(good_sjson.name)

        with self.assertRaises(ValueError):
            item.get_transcript('en')

    def test_key_error(self):
        self.item_descriptor.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        good_sjson = _create_file(content="""
                {
                  "start": [
                    270,
                    2720
                  ],
                  "end": [
                    2720,
                    5430
                  ]
                }
            """)

        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        item.sub = _get_subs_id(good_sjson.name)

        with self.assertRaises(KeyError):
            item.get_transcript('en')

def _clear_assets(location):
    store = contentstore()

    content_location = StaticContent.compute_location(
        location.org, location.course, location.name
    )

    assets, __ = store.get_all_content_for_course(content_location)
    for asset in assets:
        asset_location = Location(asset["_id"])
        del_cached_content(asset_location)
        id = StaticContent.get_id_from_location(asset_location)
        store.delete(id)

def _get_subs_id(filename):
        basename = os.path.splitext(os.path.basename(filename))[0]
        return basename.replace('subs_', '').replace('.srt', '')

def _create_file(content=''):
    sjson_file = tempfile.NamedTemporaryFile(prefix="subs_", suffix=".srt.sjson")
    sjson_file.content_type = 'application/json'
    sjson_file.write(textwrap.dedent(content))
    sjson_file.seek(0)
    return sjson_file

def _upload_sjson_file(file, location, default_filename='subs_{}.srt.sjson'):
    filename = default_filename.format(_get_subs_id(file.name))
    _upload_file(file, location, filename)

def _upload_file(file, location, filename):
    mime_type = file.content_type
    content_location = StaticContent.compute_location(
        location.org, location.course, filename
    )
    content = StaticContent(content_location, filename, mime_type, file.read())
    contentstore().save(content)
    del_cached_content(content.location)


