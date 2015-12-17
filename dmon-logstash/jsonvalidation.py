from jsonschema import validate

class LSValidation:
    config = {
  "type": "object",
  "properties": {
    "ESCluster": {
      "type": "string"
    },
    "LSHeap": {
      "type": "string"
    },
    "LSWorkers": {
      "type": "string"
    },
    "UDPPort": {
      "type": "string"
    }
  },
  "required": [
    "ESCluster",
    "LSHeap",
    "LSWorkers",
    "UDPPort"
  ]
}

    def validate(self, request):
        validate(request, LSValidation.config)