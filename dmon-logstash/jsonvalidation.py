from jsonschema import validate

class LSValidation:
    config = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "id": "http://jsonschema.net",
  "type": "object",
  "properties": {
    "ESCluster": {
      "id": "http://jsonschema.net/ESCluster",
      "type": "string"
    },
    "EShostIP": {
      "id": "http://jsonschema.net/EShostIP",
      "type": "string"
    },
    "EShostPort": {
      "id": "http://jsonschema.net/EShostPort",
      "type": "string"
    },
    "LSHeap": {
      "id": "http://jsonschema.net/LSHeap",
      "type": "string"
    },
    "LSWorkers": {
      "id": "http://jsonschema.net/LSWorkers",
      "type": "string"
    },
    "StormRestIP": {
      "id": "http://jsonschema.net/StormRestIP",
      "type": "string"
    },
    "StormRestPort": {
      "id": "http://jsonschema.net/StormRestPort",
      "type": "string"
    },
    "StormTopologyID": {
      "id": "http://jsonschema.net/StormTopologyID",
      "type": "string"
    },
    "UDPPort": {
      "id": "http://jsonschema.net/UDPPort",
      "type": "string"
    }
  },
  "required": [
    "ESCluster",
    "EShostIP",
    "EShostPort",
    "LSHeap",
    "LSWorkers",
    "UDPPort"
  ]
}

    def validate(self, request):
        validate(request, LSValidation.config)