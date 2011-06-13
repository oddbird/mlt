import os.path

from django import template

from ..conf import conf



register = template.Library()



class LiteralIncludeNode(template.Node):
    def __init__(self, filepath):
        self.filepath = template.Variable(filepath)


    def render(self, context):
        # @@@ Better (and Windows-compatible) path sanity checks
        filepath = os.path.join(
            conf.LITERAL_INCLUDE_ROOT,
            self.filepath.resolve(context).lstrip(os.path.sep))

        try:
            fp = open(filepath, 'r')
            output = fp.read()
            fp.close()
        except IOError:
            # @@@ More helpful error output in DEBUG mode
            output = ''

        return output


@register.tag
def literalinclude(parser, token):
    """
    Outputs the contents of a given file, path relative to LITERAL_INCLUDE_ROOT
    setting, into the page.

    """
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError(
            "'literalinclude' tag takes one argument: "
            "the path to the file to be included")
    return LiteralIncludeNode(bits[1])
