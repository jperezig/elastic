from collections import Counter
from flask import Flask, request, jsonify, abort, make_response
from dateutil.parser import parse

app = Flask(__name__)

retriever = None

counter = Counter()


def _parse_list(s):
    if s is not None:
        return s.split(',')
    return None


def _parse_date(date):
    if date is not None:
        try:
            return parse(date)
        except ValueError:
            return None
    return None


def retriever_not_ready():
    return retriever is None


def abort_server_not_ready():
    abort(make_response(jsonify(message='Server not ready'), 503))


@app.route("/search_term", methods=['GET'])
def search_term():
    if retriever_not_ready():
        abort_server_not_ready()
    if request.args.get('term') is not None:
        return jsonify(retriever.docs_by_term(request.args['term'], int(request.args.get('limit', 10))))
    else:
        abort(make_response(jsonify(message='Bad request'), 400))


@app.route("/search_range", methods=['GET'])
def search_docs_by_date():
    if retriever_not_ready():
        abort_server_not_ready()

    from_date = _parse_date(request.args.get('from', None))
    if from_date is None:
        abort(make_response(jsonify(message="Can't parse from date"), 400))

    to_date = _parse_date(request.args.get('to', None))
    if to_date is None:
        abort(make_response(jsonify(message="Can't parse to date"), 400))

    return jsonify(retriever.docs_by_range(from_date, to_date, int(request.args.get('limit', 10))))


@app.route("/search_docs", methods=['GET'])
def search_docs():
    if retriever_not_ready():
        abort_server_not_ready()
    if request.args.get('docs') is not None:
        docs = _parse_list(request.args['docs'])
        if len(docs) == 1:
            return jsonify(retriever.doc_by_id(docs[0]))
        else:
            return jsonify(retriever.docs_by_id(docs))
    else:
        abort(make_response(jsonify(message='Bad request'), 400))


@app.route("/term_stats", methods=['GET'])
def search_term_stats():
    if retriever_not_ready():
        abort_server_not_ready()
    docs = _parse_list(request.args['docs'])
    term = request.args['term']
    if docs is None or term is None:
        abort(make_response(jsonify(message='Bad request'), 400))

    return jsonify(retriever.term_stats(docs, term))


@app.route("/alert/<term>/<times>", methods=['GET'])
def alert(term, times):
    counter[term] += int(times)
    return jsonify(counter)


@app.route("/counter", methods=['GET'])
def get_counter():
    return jsonify(counter)
