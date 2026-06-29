from rest_framework import serializers


class CreateVoteSerializer(serializers.Serializer):
    vote = serializers.ChoiceField(["like", "dislike"])
