# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""Meter storage"""

from __future__ import unicode_literals

from collections import defaultdict
import six
import threading

from collectd_openstack.common.meters.base import Meter
from collectd_openstack.common.meters.libvirt import LibvirtMeter
from collectd_openstack.common.settings import Config


class MeterStorage(object):
    """Meter storage"""

    # all plugins
    _classes = {
        'libvirt': LibvirtMeter,
    }

    def __init__(self, collectd):
        self._meters = {}
        self._default = Meter(collectd=collectd)

        # fill dict with specialized meters classes
        if Config.instance().libvirt_enabled() is True:
            # Deprecated: Enabled manually
            self._meters = \
                {key: meter_class(collectd=collectd)
                 for key, meter_class in six.iteritems(self._classes)}

    def get(self, plugin):
        """Get meter for the collectd plugin"""
        # return specialized meter class for collectd plugin or default Meter
        return self._meters.get(plugin, self._default)


class SampleContainer(object):
    """Temporary storage for collectd samples"""

    def __init__(self):
        self._lock = threading.Lock()
        self._data = defaultdict(list)

    def add(self, key, samples, limit):
        """Store list of samples under the key

        Store the list of samples under the given key. If the number of stored
        samples is greater than the given limit, all the samples are returned
        and the stored samples are dropped. Otherwise None is returned.

        @param key      key of the samples
        @param samples  list of samples
        @param limit    sample list limit
        """
        with self._lock:
            current = self._data[key]
            current += samples
            if len(current) >= limit:
                self._data[key] = []
                return current
        return None

    def reset(self):
        """Reset stored samples

        Returns all samples and removes them from the container.
        """
        with self._lock:
            retval = self._data
            self._data = defaultdict(list)
        return retval
