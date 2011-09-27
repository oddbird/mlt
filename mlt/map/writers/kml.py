from django.template.loader import render_to_string

from .base import AddressWriter



class KMLWriter(AddressWriter):
    mimetype = "application/vnd.google-earth.kml+xml"
    extension = "kml"


    def save(self, stream):
        def addresses(objects):
            for address in objects:
                address.serialized = self.serializer.one(address)
                yield address

        stream.write(
            render_to_string(
                "kml/base.kml", {"addresses": addresses(self.objects)}))
