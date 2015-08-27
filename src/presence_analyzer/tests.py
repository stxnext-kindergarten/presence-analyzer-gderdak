# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""

from __future__ import unicode_literals

import datetime
import json
import os.path
import unittest

from presence_analyzer import main, utils, views

TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)
TEST_DATA_XML = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_xml.xml'
)
DELETED_XML_FILE = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'deleted_xml.xml'
)
# pylint: disable=maybe-no-member, too-many-public-methods


class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'DATA_XML': TEST_DATA_XML})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_jsonify(self):
        """
        Tests response from jsonify fuction.
        """
        expected_data = utils.jsonify(lambda: {'key': 'value'})()
        data = json.loads(expected_data.data)
        self.assertDictEqual(data, {'key': 'value'})
        self.assertEqual(expected_data.status_code, 200)
        self.assertEqual(expected_data.content_type, 'application/json')

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.content_type, 'text/html; charset=utf-8')
        assert resp.headers['Location'].endswith('/presence_weekday')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status_code, 200)
        test_data = json.loads(resp.data)
        self.assertEqual(len(test_data), 2)
        self.assertDictEqual(
            test_data[0],
            {
                'name': 'Adam P.',
                'avatar': 'https://intranet.stxnext.pl:443/api/images/users/141',
                'user_id': 141
            }
        )
        main.app.config.update({'DATA_XML': DELETED_XML_FILE})
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.content_type, 'text/html')

    def test_mean_time_weekday_view(self):
        """
        Test user total presence grouped by weekday.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/1')
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        test_data = json.loads(resp.data)
        self.assertListEqual(
            test_data,
            [
                ['Mon', 0],
                ['Tue', 30047.0],
                ['Wed', 24465.0],
                ['Thu', 23705.0],
                ['Fri', 0],
                ['Sat', 0],
                ['Sun', 0]
            ]
        )

    def test_presence_weekday_view(self):
        """
        Test user total presence grouped by weekday.
        """
        resp = self.client.get('/api/v1/presence_weekday/1')
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        test_data = json.loads(resp.data)
        self.assertListEqual(
            test_data,
            [
                ['Weekday', 'Presence (s)'],
                ['Mon', 0],
                ['Tue', 30047],
                ['Wed', 24465],
                ['Thu', 23705],
                ['Fri', 0],
                ['Sat', 0],
                ['Sun', 0]
            ]
        )

    def test_mean_presence_hours_view(self):
        """
        Test mean presence time view.
        """
        response = self.client.get('/api/v1/presence_start_end/1')
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/api/v1/presence_start_end/10')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        test_data = json.loads(response.data)
        self.assertListEqual(
            test_data,
            [
                ['Mon', 0, 0],
                ['Tue', 34745.0, 64792.0],
                ['Wed', 33592.0, 58057.0],
                ['Thu', 38926.0, 62631.0],
                ['Fri', 0, 0],
                ['Sat', 0, 0],
                ['Sun', 0, 0]
            ]
        )

    def test_render_template(self):
        """"
        Test for rendering templates for given url.
        """
        response = self.client.get('/test_page')
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/test_template')
        self.assertEqual(response.status_code, 500)
        response = self.client.get('/presence_weekday')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/html; charset=utf-8')


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        test_data = utils.get_data()
        self.assertEqual(len(test_data), 2)
        self.assertIsInstance(test_data, dict)
        self.assertListEqual(test_data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, test_data[10])
        self.assertItemsEqual(
            test_data[10][sample_date].keys(),
            ['start', 'end']
        )
        self.assertEqual(
            test_data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_group_by_weekday(self):
        """
        Test for grouped presence entries by weekday.
        """
        test_data = utils.get_data()
        self.assertEqual(type(test_data), dict)
        self.assertListEqual(test_data.keys(), [10, 11])
        result = utils.group_by_weekday(test_data[10])
        self.assertListEqual(
            result,
            [[], [30047], [24465], [23705], [], [], []]
        )

    def test_seconds_since_midnight(self):
        """
        Test for calculating seconds since midnight.
        """
        result = utils.seconds_since_midnight(datetime.time(1, 1, 0))
        self.assertLessEqual(result, 86399)
        self.assertEqual(result, 3660)

    def test_interval(self):
        """
        Tests of calculating time in sec. between two datetime.time objects.
        """
        result = utils.interval(
            datetime.time(0, 0, 0),
            datetime.time(23, 59, 59)
        )
        self.assertEqual(result, 86399)

    def test_mean(self):
        """
        Testing for calculating arithmetic mean in mean functions.
        """
        self.assertEqual(utils.mean([2, 3.25, 5, 10, 5.4]), 5.13)
        self.assertEqual(utils.mean([]), 0)
        self.assertEqual(utils.mean([-1, -3]), -2)

    def test_mean_presence_hours(self):
        """
        Test for calculate mean presence start/end time of given user.
        """
        data = utils.get_data()
        test_user = utils.mean_presence_hours(data[10])
        self.assertListEqual(
            test_user,
            [
                ['Mon', 0, 0],
                ['Tue', 34745.0, 64792.0],
                ['Wed', 33592.0, 58057.0],
                ['Thu', 38926.0, 62631.0],
                ['Fri', 0, 0],
                ['Sat', 0, 0],
                ['Sun', 0, 0]
            ]
        )


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
