from .. import serializers



class BaseWriter(object):
    """
    A writer writes data about objects in a given file format (e.g. CSV, XLS,
    SHP, KML). A writer is instantiated with an iterable of objects. When its
    ``save`` method is called (and passed a writable stream), the output is
    written to that stream.

    """
    def __init__(self, objects):
        self.objects = objects


    mimetype = "text/plain"
    extension = "txt"
    # subclasses should set to True if they access mapped-parcel data
    needs_parcels = False


    serializer = serializers.Serializer()


    def serialized(self):
        return self.serializer.many(self.objects)


    @property
    def field_names(self):
        return self.serializer.fields


    def save(self, stream):
        raise NotImplementedError(
            "BaseWriter subclasses should override save()")



class AddressWriter(BaseWriter):
    serializer = serializers.AddressSerializer()
