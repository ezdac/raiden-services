import gevent
from eth_utils import is_address, is_checksum_address
from flask import Flask
from flask_restful import Resource, Api, reqparse
from gevent import Greenlet  # flake8: noqa
from gevent.pywsgi import WSGIServer

from pathfinder.config import API_DEFAULT_PORT, API_HOST, API_PATH
from pathfinder.pathfinder import Pathfinder


class PathfinderResource(Resource):
    def __init__(self, pathfinder: Pathfinder):
        self.pathfinder = pathfinder


class ChannelBalanceResource(PathfinderResource):
    def put(self, channel_id: str):
        pass


class ChannelFeeResource(PathfinderResource):
    def put(self, channel_id: str):
        pass


class PathsResource(PathfinderResource):
    @staticmethod
    def _validate_args(args):
        required_args = ['from', 'to', 'value', 'num_paths']
        if not all(args[arg] is not None for arg in required_args):
            return {'error': 'Required parameters: {}'.format(required_args)}, 400

        address_error = 'Invalid {} address: {}'
        if not is_address(args['from']):
            return {'error': address_error.format('initiator', args['from'])}, 400
        if not is_address(args['to']):
            return {'error': address_error.format('target', args['to'])}, 400

        address_error = '{} address not checksummed: {}'
        if not is_checksum_address(args['from']):
            return {'error': address_error.format('Initiator', args['from'])}, 400
        if not is_checksum_address(args['to']):
            return {'error': address_error.format('Target', args['to'])}, 400

        if args.value < 0:
            return {'error': 'Payment value must be non-negative: {}'.format(args.value)}, 400

        if args.num_paths <= 0:
            return {'error': 'Number of paths must be positive: {}'.format(args.num_paths)}, 400

        return None

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('from', type=str, help='Payment initiator address.')
        parser.add_argument('to', type=str, help='Payment target address.')
        parser.add_argument('value', type=int, help='Maximum payment value.')
        parser.add_argument('num_paths', type=int, help='Number of paths requested.')

        args = parser.parse_args()
        error = self._validate_args(args)
        if error is not None:
            return error


class PaymentInfoResource(Resource):
    def __init__(self):
        pass


class ServiceApi:
    def __init__(self, pathfinder: Pathfinder):
        self.flask_app = Flask(__name__)
        self.api = Api(self.flask_app)
        self.rest_server = None  # type: WSGIServer
        self.server_greenlet = None  # type: Greenlet

        resources = [
            ('/channels/<channel_id>/balance', ChannelBalanceResource, {}),
            ('/channels/<channel_id>/fee', ChannelFeeResource, {}),
            ('/paths', PathsResource, {}),
            ('/payment/info', PaymentInfoResource, {})
        ]

        for endpoint_url, resource, kwargs in resources:
            endpoint_url = API_PATH + endpoint_url
            kwargs['pathfinder'] = pathfinder
            self.api.add_resource(resource, endpoint_url, resource_class_kwargs=kwargs)

    def run(self, port: int = API_DEFAULT_PORT):
        self.rest_server = WSGIServer((API_HOST, port), self.flask_app)
        self.server_greenlet = gevent.spawn(self.rest_server.serve_forever)
