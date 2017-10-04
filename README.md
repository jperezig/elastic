 # Pull Docker Image
```docker pull jperezig/elastic```

# Run Elasticsearch
```docker run --rm -p 9200:9200 -p 5000:5000 --name index_service jperezig/elastic```
# Run Endpoint
 ```docker exec -it index_service python3 /root/index_service.py server /root/index_service.conf```

# Run Ingester 
 ```docker exec -it index_service python3  /root/index_service.py ingester PASSWORD /root/index_service.conf -v```

 # API Endpoint
 ### Return documents which contain a specific term:
 ```curl -v "localhost:5000/search_term?term=hello&limit=10"```
### Return document(s) per id(s):
 ```curl -v "localhost:5000/search_docs?docs=AV7sMvLsuCIpkqV5n2CK,BV7sMvLsuCIpkqV5n2CK,CV7sMvLsuCIpkqV5n2CK"```
### Return documents ingested in a date range):
```curl -v "localhost:5000/search_range?from=2017-10-05T11:02:24&to=2017-10-05T11:02:25&limit=10"```
### Return statistics of a term in a subset of documents:
 ```curl -v "localhost:5000/term_stats?term=hello&docs=AV7sMvLsuCIpkqV5n2CK,BV7sMvLsuCIpkqV5n2CK,CV7sMvLsuCIpkqV5n2CK"```
 
 This endpoint returns:
  - the aggregate frequency among the subset of documents (freq)
  - the global frequency among the collection (total_freq)
  - the number of documents where the term appears (doc_freq)
### Increment in n the number of times a keyword has been observed:
```curl -v "localhost:5000/alert/hello/12"```
### Return the number of times a subset of keywords was observed during ingestion. The subset of keywords is fixed in the configuration file:
```curl -v "localhost:5000/counter"```
