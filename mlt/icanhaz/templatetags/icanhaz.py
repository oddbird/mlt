import os.path

from django import template

from ..conf import conf



register = template.Library()



class ICanHazNode(template.Node):
    def __init__(self, name):
        self.name = template.Variable(name)


    def render(self, context):
        # @@@ Name/path sanity checks
        name = self.name.resolve(context)
        filepath = os.path.join(
            conf.ICANHAZ_DIR,
            name + ".html")

        try:
            fp = open(filepath, 'r')
            output = fp.read()
            fp.close()
            output = ('<script id="%s" type="text/html">\n'
                      % name) + output + "\n</script>\n"
        except IOError:
            # @@@ More helpful error output in DEBUG mode
            output = ''

        return output


@register.tag
def icanhaz(parser, token):
    """
    Outputs the contents of a given file, path relative to ICANHAZ_DIR
    setting, into the page.

    """
    bits = token.contents.split()
    if len(bits) not in [2, 3]:
        raise template.TemplateSyntaxError(
            "'icanhaz' tag takes one argument: the name/id of the template")
    return ICanHazNode(bits[1])
