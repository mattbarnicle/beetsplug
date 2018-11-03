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

"""Copy data from one tag to another
"""

import sys

from beets.plugins import BeetsPlugin
from beets.ui import Subcommand, decargs

class TagCopy(BeetsPlugin):
  is_only_empty_tags_enabled = None

  def __init__(self):
    super(TagCopy, self).__init__()

    # set config defaults
    self.config.add({
      'only_empty_tags': False,
      'copy_tags': []
    })

    self.is_only_empty_tags_enabled = self.config['only_empty_tags'].get()

    self.import_stages = [self.tracks_imported]

  def get_copy_tag_defs(self):
    copy_tag_defs = []

    for copy_tag_def in self.config['copy_tags'].as_str_seq():
      copy_tag_defs.append(copy_tag_def.split('='))

    return copy_tag_defs

  def commands(self):
    tag_copy_command = Subcommand(
      'tagcopy',
      help = 'copy the contents of one tag to another',
      aliases = ['tc']
    )

    def copy_tags(lib, opts, args):
      items = list(lib.items(decargs(args)))

      for item in items:
        item = self.process_item(item)
        item.store()
        item.write()

    tag_copy_command.func = copy_tags

    return [tag_copy_command]

  def tracks_imported(self, session, task):
    for item in task.imported_items():
      item = self.process_item(item)
      item.store()

  def process_item(self, item):
    for copy_to, copy_from in self.get_copy_tag_defs():

      if self.is_only_empty_tags_enabled:
        if not item[copy_to]:
          item[copy_to] = item[copy_from]
      else:
        item[copy_to] = item[copy_from]

      return item
