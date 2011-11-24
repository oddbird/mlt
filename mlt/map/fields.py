from django.db import models



class CICharField(models.CharField):
    """
    A CharField that uses the CITEXT data type in Postgres 8.4+ to achieve
    case-insensitive comparison and sorting.

    """
    def db_type(self, connection):
        return "citext"


from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^mlt\.map\.fields\.CICharField"])
