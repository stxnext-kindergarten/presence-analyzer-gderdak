# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import calendar
import csv
import logging
import time

from datetime import datetime
from flask import Response
from functools import wraps
from json import dumps
from threading import Lock

from presence_analyzer.main import APP

CACHE_STORAGE = {}
LOG = logging.getLogger(__name__)


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


def memoize(duration_time):
    """
    Cache function response for a given amount of time in seconds.
    """
    lock = Lock()

    def _memoize(function):
        """
        This docstring will be overridden.
        """
        @wraps(function)
        def __memoize(*args, **kwargs):
            """
            This docstring will be overridden by @wraps decorator.
            """
            f_name = function.__name__
            arguments = [str(arg) for arg in args]
            kwarguments = [
                '%s:%s' % (key, hash(value)) for key, value in kwargs.items()
            ]
            time_now = int(time.time())
            key = '{}{}{}'.format(f_name, arguments, kwarguments)
            with lock:
                if (key in CACHE_STORAGE and
                        time_now - CACHE_STORAGE[key]['time'] < duration_time):
                    return CACHE_STORAGE[key]['value']
                value = function(*args, **kwargs)
                CACHE_STORAGE[key] = {
                    'time': time_now,
                    'value': value
                }
                return value
        return __memoize
    return _memoize


@memoize(600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(APP.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                LOG.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}
    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def seconds_since_midnight(time_data):
    """
    Calculates amount of seconds since midnight.
    """
    return time_data.hour * 3600 + time_data.minute * 60 + time_data.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def mean_presence_hours(items):
    """
    Calculate start and end of presence time of given user grouped by weekday.
    """
    week = {i: {'start': [], 'end': []} for i in xrange(7)}
    for day in items:
        week[day.weekday()]['start'].append(
            seconds_since_midnight(items[day]['start'])
        )
        week[day.weekday()]['end'].append(
            seconds_since_midnight(items[day]['end'])
        )
    return [
        [calendar.day_abbr[k], mean(v['start']), mean(v['end'])]
        for k, v in week.iteritems()
    ]


def parse_tree(root):
    """
    Parsing xml root.
    """
    server = {item.tag: item.text for item in root.getroot().find('server')}
    url = '{}://{}:{}'.format(
        server['protocol'],
        server['host'],
        server['port']
    )
    users_from_xml = root.getroot().find('users')
    return [
        {
            'user_id': int(user.get('id')),
            'name': user.find('name').text,
            'avatar': '{}{}'.format(url, user.find('avatar').text)
        }
        for user in users_from_xml
    ]


def get_all_days():
    """
    Get list of all day dates from data.
    """
    data = get_data()
    days = {}
    days = {
        int(day.strftime('%y%m%d')): day.strftime('%d.%m.%y')
        for user in data.keys()
        for day in data[user]
        if day.strftime('%d.%m.%y') not in days
    }
    return days


def get_employees(given_date):
    """
    Get list of employees that have been working at given date.
    """
    data = get_data()
    date_object = datetime.strptime(str(given_date), "%y%m%d").date()
    employees = {
        user: interval(data[user][date]['start'], data[user][date]['end'])
        for user in data
        for date in data[user]
        if date == date_object
    }
    return employees
