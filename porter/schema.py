"""
 This file is part of nucypher.

 nucypher is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 nucypher is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with nucypher.  If not, see <https://www.gnu.org/licenses/>.
"""


import click
from marshmallow import fields as marshmallow_fields, Schema, INCLUDE
from marshmallow import validates_schema

from nucypher.cli import types
from porter import fields
from porter.fields.exceptions import InvalidArgumentCombo, InvalidInputData
from porter.fields.key import Key
from porter.fields.retrieve import RetrievalKit, RetrievalOutcomeSchema
from porter.fields.treasuremap import TreasureMap
from porter.specifications import fields as base_fields


class BaseSchema(Schema):

    class Meta:
        unknown = INCLUDE   # pass through any data that isn't defined as a field

    def handle_error(self, error, data, many, **kwargs):
        raise InvalidInputData(error)


def option_ursula():
    return click.option(
        '--ursula',
        '-u',
        help="Ursula checksum address",
        type=types.EIP55_CHECKSUM_ADDRESS,
        required=True)


def option_bob_encrypting_key():
    return click.option(
        '--bob-encrypting-key',
        '-bek',
        help="Bob's encrypting key as a hexadecimal string",
        type=click.STRING,
        required=True)


#
# Alice Endpoints
#


class AliceGetUrsulas(BaseSchema):
    quantity = base_fields.PositiveInteger(
        required=True,
        load_only=True,
        click=click.option(
            '--quantity',
            '-n',
            help="Total number of Ursulas needed",
            type=click.INT, required=True))

    # optional
    exclude_ursulas = base_fields.StringList(
        fields.UrsulaChecksumAddress(),
        click=click.option(
            '--exclude-ursula',
            '-e',
            help="Ursula checksum address to exclude from sample",
            multiple=True,
            type=types.EIP55_CHECKSUM_ADDRESS,
            required=False,
            default=[]),
        required=False,
        load_only=True)

    include_ursulas = base_fields.StringList(
        fields.UrsulaChecksumAddress(),
        click=click.option(
            '--include-ursula',
            '-i',
            help="Ursula checksum address to include in sample",
            multiple=True,
            type=types.EIP55_CHECKSUM_ADDRESS,
            required=False,
            default=[]),
        required=False,
        load_only=True)

    # output
    ursulas = marshmallow_fields.List(marshmallow_fields.Nested(fields.UrsulaInfoSchema), dump_only=True)
    
    @validates_schema
    def check_valid_quantity_and_include_ursulas(self, data, **kwargs):
        # TODO does this make sense - perhaps having extra ursulas could be a good thing if some are down or can't
        #  be contacted at that time
        ursulas_to_include = data.get('include_ursulas')
        if ursulas_to_include and len(ursulas_to_include) > data['quantity']:
            raise InvalidArgumentCombo(f"Ursulas to include is greater than quantity requested")

    @validates_schema
    def check_include_and_exclude_are_mutually_exclusive(self, data, **kwargs):
        ursulas_to_include = data.get('include_ursulas') or []
        ursulas_to_exclude = data.get('exclude_ursulas') or []
        common_ursulas = set(ursulas_to_include).intersection(ursulas_to_exclude)
        if len(common_ursulas) > 0:
            raise InvalidArgumentCombo(f"Ursulas to include and exclude are not mutually exclusive; "
                                       f"common entries {common_ursulas}")


class AliceRevoke(BaseSchema):
    pass  # TODO need to understand revoke process better


#
# Bob Endpoints
#

class BobRetrieveCFrags(BaseSchema):
    treasure_map = TreasureMap(
        required=True,
        load_only=True,
        click=click.option(
            '--treasure-map',
            '-t',
            help="Unencrypted Treasure Map for retrieval",
            type=click.STRING,
            required=True))
    retrieval_kits = base_fields.StringList(
        RetrievalKit(),
        click=click.option(
            '--retrieval-kits',
            '-r',
            help="Retrieval kits for reencryption",
            multiple=True,
            type=click.STRING,
            required=True,
            default=[]),
        required=True,
        load_only=True)
    alice_verifying_key = Key(
        required=True,
        load_only=True,
        click=click.option(
            '--alice-verifying-key',
            '-avk',
            help="Alice's verifying key as a hexadecimal string",
            type=click.STRING,
            required=True))
    bob_encrypting_key = Key(
        required=True,
        load_only=True,
        click=option_bob_encrypting_key())
    bob_verifying_key = Key(
        required=True,
        load_only=True,
        click=click.option(
            '--bob-verifying-key',
            '-bvk',
            help="Bob's verifying key as a hexadecimal string",
            type=click.STRING,
            required=True))

    # optional
    context = base_fields.JSON(
        expected_type=dict,
        required=False,
        load_only=True,
        click=click.option(
            "--context",
            "-ctx",
            help="Context data for retrieval conditions",
            type=click.STRING,
            required=False,
        ),
    )

    # output
    retrieval_results = marshmallow_fields.List(
        marshmallow_fields.Nested(RetrievalOutcomeSchema), dump_only=True
    )
