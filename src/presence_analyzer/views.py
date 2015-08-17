# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
import jinja2
import logging

from flask import abort, redirect, render_template, url_for
from presence_analyzer.main import app
from presence_analyzer.utils import (
    get_data, group_by_weekday, jsonify, mean, mean_presence_hours
)

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect(url_for(
        'render_correct_template',
        template_name='presence_weekday'
    ))


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [
        {'user_id': i, 'name': 'User {0}'.format(str(i))}
        for i in data.keys()
    ]


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def mean_presence_hours_view(user_id):
    """
    Returns start and end of presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)
    return mean_presence_hours(data[user_id])


@app.route('/<template_name>', methods=['GET'])
def render_correct_template(template_name):
    """
    Check and render correct template for given url.
    """
    try:
        return render_template(template_name + '.html')
    except jinja2.TemplateNotFound:
        log.debug('Template %s not found!', template_name + '.html')
        abort(404)
    except jinja2.TemplateSyntaxError:
        log.debug('Template syntax error in %s!', template_name + '.html')
        abort(500)
