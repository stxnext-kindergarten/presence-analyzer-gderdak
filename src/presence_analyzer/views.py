# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
import logging

from flask import abort, redirect, url_for
from flask_mako import render_template
from lxml import etree
from mako import exceptions
from mako.exceptions import TopLevelLookupException

from presence_analyzer.main import APP
from presence_analyzer.utils import (
    get_data, group_by_weekday, jsonify, mean, mean_presence_hours,
    parse_tree, get_all_days, get_employees
)

LOG = logging.getLogger(__name__)


@APP.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect(url_for(
        'render_correct_template',
        template_name='presence_weekday'
    ))


@APP.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    try:
        tree = etree.parse(APP.config['DATA_XML'])
        users = parse_tree(tree)
    except IOError:
        LOG.exception('FileError!')
        abort(404)
    except ValueError:
        LOG.exception('ParsingError!')
        abort(500)
    else:
        return users


@APP.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        LOG.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]
    return result


@APP.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        LOG.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@APP.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def mean_presence_hours_view(user_id):
    """
    Returns start and end of presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        LOG.debug('User %s not found!', user_id)
        abort(404)
    return mean_presence_hours(data[user_id])


@APP.route('/api/v1/days/', methods=['GET'])
@jsonify
def view_all_days():
    """
    Dates listing for dropdown.
    """
    return sorted(get_all_days().items())


@APP.route('/api/v1/top_five/<int:given_date>', methods=['GET'])
@jsonify
def view_top_five_employees(given_date):
    """
    Returns five top employees that have longest presence time at given date.
    """
    days = get_all_days()
    if given_date not in days:
        LOG.debug('Wrong date (%s) or date doesn\'t exist.', given_date)
        abort(404)
    return sorted(
        get_employees(given_date).items(),
        key=lambda val: val[1],
        reverse=True
    )


@APP.route('/<template_name>', methods=['GET'])
def render_correct_template(template_name):
    """
    Check and render correct template for given url.
    """
    try:
        return render_template(template_name + '.html')
    except TopLevelLookupException:
        LOG.debug('Template %s.html not found.', template_name)
        abort(404)
    except exceptions.html_error_template().render():
        LOG.debug('Template error in %s.html.', template_name)
        abort(500)
