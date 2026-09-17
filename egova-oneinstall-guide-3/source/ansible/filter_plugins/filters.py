# -*- coding:utf-8 -*-
import base64
import datetime
import glob
import json
import os.path
import pipes
import re
import sys
import types
from random import SystemRandom

import yaml
from ansible import errors
from jinja2.filters import environmentfilter

reload(sys)
sys.setdefaultencoding('utf8')


def to_nice_yaml(*a, **kw):
    '''Make verbose, human readable yaml'''
    return yaml.safe_dump(*a, indent=4, allow_unicode=True, default_flow_style=False, **kw)


def to_json(a, *args, **kw):
    ''' Convert the value to JSON '''
    return json.dumps(a, *args, **kw)


def to_nice_json(a, *args, **kw):
    '''Make verbose, human readable JSON'''
    return json.dumps(a, indent=4, sort_keys=True, *args, **kw)


def failed(*a, **kw):
    ''' Test if task result yields failed '''
    item = a[0]
    if type(item) != dict:
        raise errors.AnsibleFilterError("|failed expects a dictionary")
    rc = item.get('rc', 0)
    failed = item.get('failed', False)
    if rc != 0 or failed:
        return True
    else:
        return False


def success(*a, **kw):
    ''' Test if task result yields success '''
    return not failed(*a, **kw)


def changed(*a, **kw):
    ''' Test if task result yields changed '''
    item = a[0]
    if type(item) != dict:
        raise errors.AnsibleFilterError("|changed expects a dictionary")
    if not 'changed' in item:
        changed = False
        if ('results' in item  # some modules return a 'results' key
                and type(item['results']) == list
                and type(item['results'][0]) == dict):
            for result in item['results']:
                changed = changed or result.get('changed', False)
    else:
        changed = item.get('changed', False)
    return changed


def skipped(*a, **kw):
    ''' Test if task result yields skipped '''
    item = a[0]
    if type(item) != dict:
        raise errors.AnsibleFilterError("|skipped expects a dictionary")
    skipped = item.get('skipped', False)
    return skipped


def mandatory(a):
    ''' Make a variable mandatory '''
    try:
        a
    except NameError:
        raise errors.AnsibleFilterError('Mandatory variable not defined.')
    else:
        return a


def bool(a):
    ''' return a bool for the arg '''
    if a is None or type(a) == bool:
        return a
    if type(a) in types.StringTypes:
        a = a.lower()
    if a in ['yes', 'on', '1', 'true', 1]:
        return True
    else:
        return False


def quote(a):
    ''' return its argument quoted for shell usage '''
    return pipes.quote(a)


def fileglob(pathname):
    ''' return list of matched files for glob '''
    return glob.glob(pathname)


def regex(value='', pattern='', ignorecase=False, match_type='search'):
    ''' Expose `re` as a boolean filter using the `search` method by default.
        This is likely only useful for `search` and `match` which already
        have their own filters.
    '''
    if ignorecase:
        flags = re.I
    else:
        flags = 0
    _re = re.compile(pattern, flags=flags)
    _bool = __builtins__.get('bool')
    return _bool(getattr(_re, match_type, 'search')(value))


def match(value, pattern='', ignorecase=False):
    ''' Perform a `re.match` returning a boolean '''
    return regex(value, pattern, ignorecase, 'match')


def search(value, pattern='', ignorecase=False):
    ''' Perform a `re.search` returning a boolean '''
    return regex(value, pattern, ignorecase, 'search')


def regex_replace(value='', pattern='', replacement='', ignorecase=False):
    ''' Perform a `re.sub` returning a string '''

    if not isinstance(value, basestring):
        value = str(value)

    if ignorecase:
        flags = re.I
    else:
        flags = 0
    _re = re.compile(pattern, flags=flags)
    return _re.sub(replacement, value)


def unique(a):
    return set(a)


def intersect(a, b):
    return set(a).intersection(b)


def difference(a, b):
    return set(a).difference(b)


def symmetric_difference(a, b):
    return set(a).symmetric_difference(b)


def union(a, b):
    return set(a).union(b)


''' 获取微服务部署的节点信息'''


def get_ms_node(ms_dict):
    nodes = []
    backends = []
    url_backend = ""
    url_frontend = ""

    for ms_name, v in ms_dict.iteritems():
        if ms_dict[ms_name]["status"] == "success":
            nodes.append(ms_dict[ms_name]["host"])
            backends.append({'host': ms_dict[ms_name]["host"], 'port': str(ms_dict[ms_name]["server_port"])})
            if ms_dict[ms_name]["url"]:
                if ms_dict[ms_name]["url"]["frontend"] and url_frontend == "":
                    url_frontend = ms_dict[ms_name]["url"]["frontend"]
                if ms_dict[ms_name]["url"]["backend"] and url_backend == "":
                    url_backend = ms_dict[ms_name]["url"]["backend"]

    return {'nodes': nodes, 'backends': backends, 'url_backend': url_backend, 'url_frontend': url_frontend}


def is_dict(obj):
    return type(obj) == types.DictType


def is_list(obj):
    return type(obj) == types.ListType


"""
格式化B字节相关
"""


def format_size(size, unit):
    size_unit = {0: '', 1: 'B', 2: 'KB', 3: 'MB', 4: 'GB', 5: 'TB', 6: 'PB'}
    n = 0
    for power, ut in size_unit.iteritems():
        if unit == ut:
            n = power
            break
    while size > 1024 and n < 6:
        size /= 1024.0
        n += 1
    return "{0:.2f}{1}".format(size, size_unit[n])


def translate(source, dict):
    if dict and dict.has_key(source.lower()):
        return dict[source.lower()]
    return source


"""
大数格式化
例：
  12345 > 123,45
  1245.34 > 124,5.34
"""


def format_big_number(data):
    try:
        result = str(data).strip()
        result_arr = result.split('.')
        if len(result_arr) > 1:
            tmp = '{:.2f}'.format(float(result))
            return '{:,}'.format(tmp)
        else:
            return '{:,}'.format(int(result))
    except:
        return data


def format_unixtime(data):
    return datetime.datetime.fromtimestamp(float(data)).strftime("%Y-%m-%d %H:%M:%S")


@environmentfilter
def rand(environment, end, start=None, step=None):
    r = SystemRandom()
    if isinstance(end, (int, long)):
        if not start:
            start = 0
        if not step:
            step = 1
        return r.randrange(start, end, step)
    elif hasattr(end, '__iter__'):
        if start or step:
            raise errors.AnsibleFilterError('start and step can only be used with integer values')
        return r.choice(end)
    else:
        raise errors.AnsibleFilterError('random can only be used on sequences and integers')


class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            # base 64
            'b64decode': base64.b64decode,
            'b64encode': base64.b64encode,

            # json
            'to_json': to_json,
            'to_nice_json': to_nice_json,
            'from_json': json.loads,

            # yaml
            'to_yaml': yaml.safe_dump,
            'to_nice_yaml': to_nice_yaml,
            'from_yaml': yaml.safe_load,

            # path
            'basename': os.path.basename,
            'dirname': os.path.dirname,
            'expanduser': os.path.expanduser,
            'realpath': os.path.realpath,
            'relpath': os.path.relpath,

            # failure testing
            'failed': failed,
            'success': success,

            # changed testing
            'changed': changed,

            # skip testing
            'skipped': skipped,

            # variable existence
            'mandatory': mandatory,

            # value as boolean
            'bool': bool,

            # quote string for shell usage
            'quote': quote,

            # file glob
            'fileglob': fileglob,

            # regex
            'match': match,
            'search': search,
            'regex': regex,
            'regex_replace': regex_replace,

            # list
            'unique': unique,
            'intersect': intersect,
            'difference': difference,
            'symmetric_difference': symmetric_difference,
            'union': union,

            # random numbers
            'random': rand,
            'is_list': is_list,
            'is_dict': is_dict,
            'translate': translate,
            'format_unixtime': format_unixtime,
            # 微服务节点信息
            'get_ms_node': get_ms_node
        }
