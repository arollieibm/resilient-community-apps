# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.
"""Tests using pytest_resilient_circuits"""

from __future__ import print_function
import pytest
# Imports used for testing
import mock
from mock import patch
import json
import pika
from resilient_circuits.util import get_config_data, get_function_definition
from resilient_circuits import SubmitTestFunction, FunctionResult
# Testing helpers and classes to mock
from fn_icdx.util.amqp_facade import AmqpFacade
from fn_icdx.util.helper import ICDXHelper
from amqpmock import AmqpFacadeMock, mocked_call

PACKAGE_NAME = "fn_icdx"
FUNCTION_NAME = "icdx_get_event"

# Read the default configuration-data section from the package
config_data = get_config_data(PACKAGE_NAME)

# Provide a simulation of the Resilient REST API (uncomment to connect to a real appliance)
resilient_mock = "pytest_resilient_circuits.BasicResilientMock"


def call_icdx_get_event_function(circuits, function_params, timeout=20):
    # Fire a message to the function
    evt = SubmitTestFunction("icdx_get_event", function_params)
    circuits.manager.fire(evt)
    event = circuits.watcher.wait("icdx_get_event_result", parent=evt, timeout=timeout)
    assert event
    assert isinstance(event.kwargs["result"], FunctionResult)
    pytest.wait_for(event, "complete", True)
    return event.kwargs["result"].value


class TestIcdxGetEvent:
    """ Tests for the icdx_utilities_get_event function"""

    def test_function_definition(self):
        """ Test that the package provides customization_data that defines the function """
        func = get_function_definition(PACKAGE_NAME, FUNCTION_NAME)
        assert func is not None

    @pytest.mark.parametrize("icdx_uuid, expected_results", [
        ("ec6167c0-1c2e-11e8-c000-000000000022", {"value": "xyz"})
    ])
    def test_success(self, circuits_app, icdx_uuid, expected_results):
        """ Test calling with sample values for the parameters """
        function_params = { 
            "icdx_uuid": icdx_uuid
        }
        # Mock acquiring the config options, all config options are set to '10' or 10
        with patch.object(ICDXHelper, "get_config_option", lambda x, y,z=None: "10", True):
            # Mock both the AMQP connection and the channel
            with patch('pika.BlockingConnection') as mock_block, \
                    patch.object(pika.BlockingConnection, 'channel') as mock_block_channel:
                # Mock the actual AMQP call
                with patch.object(AmqpFacade, 'call') as mock_amqp:
                    mock_amqp.return_value = mocked_call(payload=json.dumps({"id": 0, "uuid": icdx_uuid}),
                                                         success=True, operation='get_event')

                    mock_block.return_value = mock.Mock()
                    mock_block_channel.return_value = mock.Mock()
                    results = call_icdx_get_event_function(circuits_app, function_params)
                    assert (results['success'] == True)

    @pytest.mark.parametrize("icdx_uuid, expected_results", [
        ("baduuid", {"value": "xyz"}),
        ("123", {"value": "xyz"}),
        ("Љ	Щ	щ	Ӄ", {"value": "xyz"}),
        ("؟	ب	حٍ	۳", {"value": "xyz"}),
        ("	Ύ	Δ	δ	Ϡ", {"value": "xyz"}),
        ("	Ą	ą	Ĳ	ĳ", {"value": "xyz"}),
    ])
    def test_failure(self, circuits_app, icdx_uuid, expected_results):
        """ Test calling with sample values for the parameters """
        function_params = {
            "icdx_uuid": icdx_uuid
        }
        # Mock acquiring the config options, all config options are set to '10' or 10
        with patch.object(ICDXHelper, "get_config_option", lambda x, y,z=None: "10", True):
            # Mock both the AMQP connection and the channel
            with patch('pika.BlockingConnection') as mock_block, \
                    patch.object(pika.BlockingConnection, 'channel') as mock_block_channel:
                # Mock the actual AMQP call
                with patch.object(AmqpFacade, 'call') as mock_amqp:
                    mock_amqp.return_value = mocked_call(payload=json.dumps({"id": 0, "uuid": icdx_uuid}),
                                                         success=False, operation='get_event')

                    mock_block.return_value = mock.Mock()
                    mock_block_channel.return_value = mock.Mock()
                    results = call_icdx_get_event_function(circuits_app, function_params)
                    assert (results['success'] == False)

    def test_amqp_client_success(self):
        amqp_client = AmqpFacadeMock()
        result, status_code = amqp_client.call(payload=json.dumps({"id": 0}), success=True)
        assert(status_code == 200)

    def test_amqp_client_failure(self):
        amqp_client = AmqpFacadeMock()
        result, status_code = amqp_client.call(payload=json.dumps({"id": 0}), success=False)
        assert(status_code == 204)