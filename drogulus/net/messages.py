# -*- coding: utf-8 -*-
"""
Contains classes that represent messages sent down the wire between nodes on
the network. Also contains functions for encoding/decoding to/from
MessagePack. Every message contains at least three mandatory fields: uuid
(identifying the interaction), node (the ID of the sender of the message) and
version (indicating the version of Drogulus the sender is running).

Named tuples are used because they are lightweight, immutable and indexable
(thus mimicing the dict like structure of the msgpack encoded message passed
down the wire). See http://bugs.python.org/issue9391 for Hettinger's advice on
adding docstrings to namedtuples and the reason why the classes are declared
in the way that they are.
"""

# Copyright (C) 2012-2013 Nicholas H.Tollervey.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from collections import namedtuple
import msgpack
from validators import VALIDATORS
from drogulus.constants import ERRORS


class Error(namedtuple('Error',
                       ['uuid', 'node', 'code', 'title', 'details',
                        'version'])):
    """

    Represents an error message to be sent to the calling node on the network.

    * uuid - the ID of the request that generated the error.
    * node - the ID of the node sending the message.
    * code - the code that identifies the specific error.
    * title - a description of the type of error generated.
    * details - diagnostic details expressed as a dict of string key/values.
    * version - the protocol version the message conforms to.
    """
    pass


class Ping(namedtuple('Ping', ['uuid', 'node', 'version'])):
    """
    A "ping" message is sent to another node on the network to determine if it
    is still contactable.

    * uuid - the ping's request ID (a random value generated by the requestor
             that uniquely identifies the request).
    * node - the ID of the node sending the message.
    * version - the protocol version the message conforms to.
    """
    pass


class Pong(namedtuple('Pong', ['uuid', 'node', 'version'])):
    """
    A "pong" message is sent as a confirmation response. This is usually the
    result of a ping request but may be used to confirm reciept of any other
    sort of request when no further data is expected to be returned.

    * uuid - the request ID of the source of the response.
    * node - the ID of the node sending the message.
    * version - the protocol version the message conforms to.
    """
    pass


class Store(namedtuple('Store', ['uuid', 'node', 'key', 'value', 'timestamp',
                                 'expires', 'public_key', 'name', 'meta',
                                 'sig', 'version'])):
    """
    A "store" message instructs another node on the network to store the given
    key/value pair.

    * uuid - the ID of the Store request (generated by the requestee).
    * node - the ID of the node sending the message.
    * key - the SHA512 value of the compound key used as the actual key on the
            DHT.
    * value - the value to be stored in the DHT.
    * timestamp - a timestamp indicating when this key/value pair was 
                  *originally* generated as an integer representing the time 
                  in seconds since the Epoch (so called POSIX time, see
                  https://en.wikipedia.org/wiki/Unix_time).
    * expires - a timestamp indicating a point in time after which this 
                key/value pair can be removed (expired) from the DHT. Expressed
                as an integer representing the time in seconds since the Epoch
                (so called POSIX time). If the value is less than or equal to 
                zero then the key/value pair should never expire.
    * public_key - the public key of the person storing the value.
    * name - the human-readable name of the key.
    * meta - a list of tuples containing key/value strings for user defined
             metadata.
    * sig - the cryptographic signature for the value, timestamp, expires, name
            and meta fields.
    * version - the protocol version the message conforms to.

    The provenance of the message is guaranteed through cryptography:

    The 'sig' field is created with the private key of the person storing the
    key/value pair. It's derived from the SHA512 hash of the SHA512 hashes of
    the 'value', 'timestamp', 'expires', 'name' and 'meta' fields. This
    mechanism ensures that the public_key used in the compound key is valid
    (i.e. it validates the sig field given the correct SHA512 hash) and also
    ensures that the 'value', 'timestamp', 'expires', 'name' and 'meta' fields
    have not been tampered with.

    The 'key' value is a compound key. It is a SHA512 hash of the SHA512 hashes
    of the 'public_key' and 'name' fields. The 'public_key' and 'name' fields
    are used to ensure that the compound 'key' field is correct.
    """
    pass


class FindNode(namedtuple('FindNode', ['uuid', 'node', 'key', 'version'])):
    """
    A "find node" message requests k nodes from the other nodes on the network
    that are closest to the given key. The value k is the maximum number of 
    nodes that can be stored in a k-bucket and is set in the constants module.
    The original Kademlia paper both names this variable and recommends its 
    value as 20.

    * uuid - the ID of the FindNode request (generated by the requestee).
    * node - the ID of the node sending the message.
    * key - the key in the DHT that is being targetted.
    * version - the protocol version the message conforms to.
    """
    pass


class Nodes(namedtuple('Nodes', ['uuid', 'node', 'nodes', 'version'])):
    """
    A response to either a FindNode or FindValue request that contains a list
    of nodes on the DHT that are close to the requested key.

    * uuid - the ID of the request that is causing the response.
    * node - the ID of the node sending the message.
    * nodes - a list of nodes on the DHT that are close to the requested key.
    * version - the protocol version the message conforms to.
    """
    pass


class FindValue(namedtuple('FindValue', ['uuid', 'node', 'key', 'version'])):
    """
    A "find value" message will cause the other node to return the
    corresponding value if the given key is in its store. Otherwise it returns
    k nodes that it knows about that are closest to the given key.

    * uuid - the ID of the FindValue request (generated by the requestee).
    * node - the ID of the node sending the message.
    * key - the key in the DHT whose value is being requested.
    * version - the protocol version the message conforms to.
    """
    pass


class Value(namedtuple('Value', ['uuid', 'node', 'key', 'value', 'timestamp',
                                 'expires', 'public_key', 'name', 'meta',
                                 'sig', 'version'])):
    """
    A response to a FindValue request. Contains all the information known by
    the responder about the key/value pair. Such complete information can be
    used to check the provenance of the data as described in the documentation
    for the Store message described above.

    * uuid - the ID of the request that is causing the response.
    * node - the ID of the node sending the message.
    * key - the SHA512 value of the compound key used as the actual key on the
            DHT.
    * value - the value found in the DHT.
    * timestamp - a timestamp indicating when this key/value pair was 
                  *originally* generated as a floating point number 
                  representing the time in seconds since the Epoch (so called 
                  POSIX time, see https://en.wikipedia.org/wiki/Unix_time).
    * expires - a timestamp indicating a point in time after which this 
                key/value pair can be removed (expired) from the DHT. Expressed
                as an integer representing the time in seconds since the Epoch
                (so called POSIX time). If the value is less than or equal to 
                zero then the key/value pair should never expire.
    * public_key - the public key of the person who stored the value.
    * name - the human-readable name of the key.
    * meta - a list of tuples containing key/value strings for user defined
             metadata.
    * sig - the cryptographic signature for the value, timestamp, expires, name
            and meta fields.
    * version - the protocol version the message conforms to.
    """
    pass


def to_msgpack(message):
    """
    Returns a string representation of the message object encoded using
    msgpack.
    """
    name = message.__class__.__name__.lower()
    data = message._asdict()
    data['message'] = name
    return msgpack.packb(data)


def from_msgpack(raw):
    """
    Returns an instance of the correct message class given the msgpack encoded
    data in the raw string. Encapsulates a variety of cleaning and checking of
    the raw message from the (potentially dangerous) external network.
    """
    data = msgpack.unpackb(raw, use_list=False)
    message = data['message']
    # Explicit is better than implicit (Zen of Python).
    if message == 'error':
        return make_message(Error, data)
    elif message == 'ping':
        return make_message(Ping, data)
    elif message == 'pong':
        return make_message(Pong, data)
    elif message == 'store':
        return make_message(Store, data)
    elif message == 'findnode':
        return make_message(FindNode, data)
    elif message == 'nodes':
        return make_message(Nodes, data)
    elif message == 'findvalue':
        return make_message(FindValue, data)
    elif message == 'value':
        return make_message(Value, data)
    else:
        # Unknown request.
        raise ValueError(2, ERRORS[2], {'context':
                         '%s is not a valid message type.' % message})


def make_message(klass, data):
    """
    Returns an instance of the referenced namedtuple based class that is
    created from the raw data. Data will be validated and an exception raised
    if this fails.
    """
    fields = klass._fields
    args = []
    errors = {}
    # Validate the values before adding them to the argument list. Store any
    # errors so they can be reported back.
    for field in fields:
        if not field in data:
            errors[field] = 'Missing field.'
            continue
        validator = VALIDATORS[field]
        value = data[field]
        if not validator(value):
            errors[field] = 'Invalid value.'
            continue
        args.append(value)
    if errors:
        raise ValueError(2, ERRORS[2], errors)
    else:
        return klass(*args)
