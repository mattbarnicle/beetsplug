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
