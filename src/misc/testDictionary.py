nestedRange ={'gte':100,'lte':101}
queryBody= {
  'size': 100,
  'sort': {
    '@timestamp': 'desc'
  },
  'query': {
    'filtered': {
      'query': {
        'query_string': {
          'query': 'hostname:\"dice.cdh5.s4.internal\" AND serviceType:\"dfs\"',
          'analyze_wildcard': True
        }
      },
      'filter': {
        'bool': {
          'must': [
            {
              'range': {
                '@timestamp': nestedRange
              }
            }
          ],
          'must_not': []
        }
      }
    }
  },
  'fields': [
    '*',
    '_source'
  ],
  'script_fields': {},
  'fielddata_fields': [
    '@timestamp'
  ]
}







# newBody = {}

# newBody['size'] = 100
# newBody['sort'] = {'@timestamp':'desc'}
# newBody['query']={'filtered':{}} 
# #['filter']['bool']['must'] = [{'@timestamp':{'gte':100,'lte':101}}]

print queryBody
