# MIT License
#
# Copyright (c) 2018 Matt Barnicle
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Allows user to blacklist or whitelist tags to be over-written
on import from their pre-existing metadata, or specify that only
empty tags can be over-written.
"""

import sys
import copy

from beets.library import Item
from beets.importer import ImportTask, SingletonImportTask
from beets.ui import Subcommand
from beets.plugins import BeetsPlugin

class SelectiveTagging(BeetsPlugin):
  orig_items = {}

  is_only_empty_tags_enabled = False
  is_whitelist_tags_enabled = False
  is_blacklist_tags_enabled = False

  def __init__(self):
    super(SelectiveTagging, self).__init__()

    # set config defaults
    self.config.add({
      'only_empty_tags': False,
      'whitelist_tags': [],
      'blacklist_tags': []
    })

    self.is_only_empty_tags_enabled = self.config['only_empty_tags'].get()
    self.is_whitelist_tags_enabled = (len(self.config['whitelist_tags'].as_str_seq()) != 0)
    self.is_blacklist_tags_enabled = (len(self.config['blacklist_tags'].as_str_seq()) != 0)

    if self.is_whitelist_tags_enabled and self.is_blacklist_tags_enabled:
      print('You can only use whitelist_tags or blacklist_tags, not both')
      sys.exit(1)

    self.register_listener('import_task_created', self.on_import_task_created)

    self.import_stages = [self.tracks_imported]

  def on_import_task_created(self, session, task):
    items = task.items if task.is_album else [task.item]

    for item in items:
      self.orig_items[item['path']] = copy.deepcopy(item)

    return [task]

  def tracks_imported(self, session, task):
    if (
      not self.is_only_empty_tags_enabled
        and not self.is_whitelist_tags_enabled
        and not self.is_blacklist_tags_enabled
    ):
      return

    # SingletonImportTask doesn't work correctly, seems like a bug in the beets code
    if isinstance(task, SingletonImportTask):
      return

    for item in task.items:
      orig_item = self.orig_items[item['path']]

      for tag in Item._media_tag_fields:
        should_reset_tag = False

        if tag not in orig_item or orig_item[tag] == item[tag]:
          continue

        if self.is_blacklist_tags_enabled:

          if self.is_tag_blacklisted(tag):
            should_reset_tag = True
            self._log.info(u'resetting blacklisted tag {0} to {1}', tag, str(orig_item[tag]))
            print(u'resetting blacklisted tag {0} to {1}'.format(tag, str(orig_item[tag])))

          # get the intersection of non-blacklisted + empty
          elif self.is_only_empty_tags_enabled and not self.is_tag_value_empty(orig_item[tag]):
            should_reset_tag = True
            self._log.info(u'resetting non-blacklisted but non-empty tag {0} to {1}', tag, str(orig_item[tag]))
            print(u'resetting non-blacklisted but non-empty tag {0} to {1}'.format(tag, str(orig_item[tag])))

        elif self.is_whitelist_tags_enabled:

          if self.is_tag_whitelisted(tag):

            # get the intersection of whitelisted + empty
            if self.is_only_empty_tags_enabled and not self.is_tag_value_empty(orig_item[tag]):
              should_reset_tag = True
              self._log.info(u'resetting whitelisted but non-empty tag {0} to {1}', tag, str(orig_item[tag]))

          else:
            should_reset_tag = True
            self._log.info(u'resetting non-whitelisted tag {0} to {1}', tag, str(orig_item[tag]))

        elif self.is_only_empty_tags_enabled:

          if not self.is_tag_value_empty(orig_item[tag]):
            should_reset_tag = True
            self._log.info(u'resetting non-empty tag {0} to {1}', tag, str(orig_item[tag]))

        if should_reset_tag:
          item[tag] = orig_item[tag]

      item.store()

  def is_tag_value_empty(self, value):
    return not value

  def is_tag_whitelisted(self, tag):
    return tag in self.config['whitelist_tags'].as_str_seq()

  def is_tag_blacklisted(self, tag):
    return tag in self.config['blacklist_tags'].as_str_seq()
