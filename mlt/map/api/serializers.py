from django.core.urlresolvers import reverse

from .. import serializers



class ApiBatchSerializer(serializers.AddressBatchSerializer):
    default_fields = serializers.AddressBatchSerializer.default_fields + [
        "addresses_url"]


    virtual_fields = set(["addresses_url"])


    def encode_addresses_url(self, batch):
        return reverse("api_addresses") + "?batches=%s" % batch.id



class ApiAddressSerializer(serializers.AddressSerializer):
    default_fields = serializers.AddressSerializer.default_fields + [
        "batches"]


    virtual_fields = set(["batches"])


    batch_serializer = ApiBatchSerializer(exclude=["addresses_url"])


    def encode_batches(self, address):
        return self.batch_serializer.many(address.batch_tags)
