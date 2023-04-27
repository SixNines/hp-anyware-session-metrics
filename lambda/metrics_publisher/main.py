import base64
import json
import zlib
import boto3
import re
import os
from datetime import datetime

NAMESPACE = os.environ.get("metrics_namespace")

cw_client = boto3.client("cloudwatch")

# Events based on https://help.teradici.com/s/article/1395
events_definitions = [
    {
        "event_pattern": ".*MGMT_PCOIP_DATA.*Tx thread info.*(?P<bw_group>bw limit\D*(?P<bw>[\d|\.]*))\W*(?P<avg_tx_group>avg tx\D*(?P<avg_tx>[\d|\.]*))\W*(?P<avg_rx_group>avg rx\D*(?P<avg_rx>[\d|\.]*)).*",
        "name": "Bandwidth metrics",
        "metrics": [
            {"Name": "PCoIPBandwidthLimit", "Unit": "Kilobytes/Second", "group": "bw"},
            {"Name": "PCoIPAvgTx", "Unit": "Kilobytes/Second", "group": "avg_tx"},
            {"Name": "PCoIPAvgRx", "Unit": "Kilobytes/Second", "group": "avg_rx"},
        ],
    },
    {
        "event_pattern": ".*MGMT_PCOIP_DATA.*Tx thread info.*(?P<rtt_group>round trip time\D*(?P<rtt>[\d|\.]*))\W*(?P<variance_group>variance\D*(?P<variance>[\d|\.]*))\W*(?P<rto_group>rto = (?P<rto>[\d|\.]*))\W*(?P<last_group>last\D*(?P<last>[\d|\.]*))\W*(?P<max_group>max\D*(?P<max>[\d|\.]*)).*",
        "name": "Latency metrics",
        "metrics": [
            {"Name": "PCoIPRoundTripTime", "Unit": "Milliseconds", "group": "rtt"},
            {"Name": "PCoIPVariance", "Unit": "Milliseconds", "group": "variance"},
        ],
    },
    {
        "event_pattern": ".*VGMAC.*Stat frms\W*(?P<R>R\D*(?P<r_a>[\d|\.]*)/(?P<r_i>[\d|\.]*)/(?P<r_o>[\d|\.]*))\W*(?P<T>T\D*(?P<t_a>[\d|\.]*)/(?P<t_i>[\d|\.]*)/(?P<t_o>[\d|\.]*)).*(?P<loss>Loss\D*(?P<r_loss>[\d|\.]*)%/(?P<t_loss>[\d|\.]*)%).*",
        "name": "Packet loss metrics",
        "metrics": [
            {"Name": "PCoIPPackeLossR", "Unit": "Percent", "group": "r_loss"},
            {"Name": "PCoIPPackeLossT", "Unit": "Percent", "group": "t_loss"},
        ],
    },
    {
        "event_pattern": ".*MGMT_PCOIP_DATA.*ubs-BW-decr\W*(?P<decrease_loss_group>Decrease\D*(?P<decrease_loss>[\d|\.]*))\W*(?P<current_group>current\D*(?P<current>[\d|\.]*))\W*(?P<active_group>active\D*(?P<active_from>[\d|\.]*)\D*(?P<active_to>[\d|\.]*))\W*(?P<adjust_factor_group>adjust factor\D*(?P<adjust_factor>[\d|\.]*)%)\W*(?P<floor_group>floor\D*(?P<floor>[\d|\.]*))\W*",
        "name": "Floor metrics",
        "metrics": [],
    },
    {
        "event_pattern": ".*MGMT_IMG.*log \(SoftIPC\).*(?P<tbl_group>tbl\W*(?P<tbl>[\d|\.]*))\W*(?P<fps_group>fps\W*(?P<fps>[\d|\.]*))\W*(?P<q_group>quality\W*(?P<quality>[\d|\.]*)).*",
        "name": "Image metrics",
        "metrics": [
            {"Name": "PCoIPQuality", "Unit": "Percent", "group": "quality"},
            {"Name": "PCoIPFPS", "Unit": "Count", "group": "fps"},
            {"Name": "PCoIPTBL", "Unit": "Count", "group": "tbl"},
        ],
    },
    {
        "event_pattern": ".*MGMT_IMG.*log \(SoftIPC\).*(?P<group1>bits\/pixel\W*(?P<bits_pixel>[\d|\.]*))\W*(?P<group2>bits\/sec\W*(?P<bits_sec>[\d|\.]*))\W*(?P<group3>MPix\/sec\W*(?P<mpix_sec>[\d|\.]*)).*",
        "name": "Image metrics",
        "metrics": [
            {"Name": "PCoIPBitsPerPixel", "Unit": "Count", "group": "bits_pixel"},
            {"Name": "PCoIPBitsPerSec", "Unit": "Count", "group": "bits_sec"},
            {"Name": "PCoIPMpixPerSec", "Unit": "Count", "group": "mpix_sec"},
        ],
    },
]


def decode_event(event):
    decoded_event = base64.b64decode(event)
    decoded_event = zlib.decompress(decoded_event, 16 + zlib.MAX_WBITS).decode("utf-8")
    decoded_event = json.loads(decoded_event)

    return decoded_event


def convert_to_number(x):
    try:
        return int(x)
    except:
        return float(x)


def handle_event(event, instance_id, match, timestamp):
    # Get instance name from instance id
    for metric in event["metrics"]:

        cw_client.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[
                {
                    "MetricName": metric["Name"],
                    "Dimensions": [
                        {"Name": "InstanceId", "Value": instance_id},
                    ],
                    "Value": convert_to_number(match.group(metric["group"])),
                    "Unit": metric["Unit"],
                    "Timestamp": timestamp,
                },
            ],
        )


def lambda_handler(event, context):
    print(event)

    # Decode message
    decoded_event = decode_event(event["awslogs"]["data"])
    print(decoded_event)

    # Get relevant data
    log_stream = decoded_event["logStream"]
    log_events = decoded_event["logEvents"]
    instance_id = re.search("i-[a-zA-Z0-9]{17}", log_stream).group(0)

    # Iterate over all messages
    for log_event in log_events:
        message = log_event["message"]
        timestamp = datetime.utcfromtimestamp(
            int(log_event["timestamp"]) / 1000
        ).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # Iterate over messages patterns
        for event_definition in events_definitions:
            match = re.search(event_definition["event_pattern"], message)
            if match:
                print(
                    "Event matched!",
                    {"event_type": event_definition["name"], "message": message},
                )
                handle_event(event_definition, instance_id, match, timestamp)
                break
