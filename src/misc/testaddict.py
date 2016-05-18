from addict import Dict

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
                '@timestamp': {
                  'gte': 100,
                  'lte': 101
                }
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

newBody = Dict()
nestedBody = Dict()



newBody.size = 100
newBody.sort = {'@timestamp':'desc'}
#newBody.sort.timestamp = 'desc'



newBody.query.filterd.query.query_string.query = "hostname:\"dice.cdh5.s4.internal\" AND serviceTyp:\"dfs\""
newBody.query.filterd.query.query_string.analyze_wildcard = True

#nestedBody.range = {'@timestamp':{'gte':100,'lte':101}}
#nestedBody.range.timestamp.gte = 100
#nestedBody.range.timestamp.lte = 101
newBody.query.filterd.filter.bool.must = [{'@timestamp':{'gte':100,'lte':101}}]
newBody.query.filterd.filter.bool.must_not = []
newBody.fields = ['*','_source']
newBody.script_fields
newBody.fielddata_fields = ["@timestamp"]

print newBody

if set(queryBody.keys()) == set(newBody.keys()):
	print "Yup1"

if queryBody != newBody:
	print "Nope"
else:
	print "Yup"


######################

  # queryBody = Dict()
  # queryBody.size = size
  # queryBody.sort = {'@timestamp':ordering}
  # #queryBody.sort.timestamp = 'desc'



  # queryBody.query.filterd.query.query_string.query = queryString
  # queryBody.query.filterd.query.query_string.analyze_wildcard = True

  # if tstop == 'None':
  #   nestedBody = {'@timestamp':{'gte':tstart}}
  # else:
  #   nestedBody = {'@timestamp':{'gte':tstart,'lte':tstop}}
  
  # queryBody.query.filterd.filter.bool.must = [nestedBody]
  # queryBody.query.filterd.filter.bool.must_not = []
  # queryBody.fields = ['*','_source']
  # queryBody.script_fields
  # queryBody.fielddata_fields = ["@timestamp"]