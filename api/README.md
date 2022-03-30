# API Documentation

## Running the API for development

Copy the `.env` file found at the root of the PANIC folder to the `/api` folder,
navigate to the `/api` directory and do the following:

```bash
npm install           # Install project dependencies
npm run build         # Build project
./run_dev_server.sh   # Run unit tests
```

## Swagger

[Swagger](https://swagger.io/) is an API documentation tool which is used to
document the endpoints and their inputs and outputs. Swagger can be accessed
when the API is run through `https://{YOUR_IP_ADDRESS}:{API_PORT}/api-docs`

## Running tests

If you want to run the tests, navigate to the `/api` directory and do the
following:

```bash
npm install         # Install project dependencies
npm test            # Run unit tests
```

## Endpoints

### `/api-docs`

Displays the swagger api documentation tool.

### `/server/mongo/monitorablesInfo`

Returns a list of monitored sources based on the base chains requested.

#### Example Input Request

```
{
    "baseChains": [
        "chainlink",
        "cosmos",
        "general",
        "substrate"
    ]
}
```

#### Example Output Response

```
{
  "result": {
    "chainlink": {
      "ethereum": {
        "parent_id": "chain_name_51383ec9-b49e-4d03-8068-d60f5f3c9285",
        "monitored": {
          "systems": [
              {
                "system_5330c562-368b-4192-bbaf-db6638307783": "chainlink_eth_adapters"
              },
              {
                "system_d2a0a05e-c0ec-4b39-a101-d3cb5f47bc03": "chainlink_host_ocr_system"
              }
            ],
          "nodes": [],
          "github_repos": [
              {
                "repo_4ca781b6-154e-4bd0-8418-0c5debc07e54": "smartcontractkit/chainlink/"
              }
            ],
          "dockerhub_repos": [],
          "chains: [
              {
                "chain_name_51383ec9-b49e-4d03-8068-d60f5f3c9285": "chainlink ethereum"
              }
          ]
        }
      }
    },
    "cosmos": {},
    "general": {
        "general": {
          "parent_id": "GENERAL",
          "monitored": {
            "systems": [
                {
                  "system_2a8b23ee-cab6-439c-85ca-d2ba5a45c934": "arbitrum"
                }
              ],
            "nodes": [],
            "github_repos": [
                {
                    "repo_fc4dfda7-2e97-433d-98ba-8af626a989b0": "SimplyVC/panic/"
                }
              ],
            "dockerhub_repos": [],
            "chains: []
            }
        }
    },
    "substrate": {}
  }
}
```

### `server/mongo/alerts`

Retrieves a list of alerts sorted by time for the requested chains, sources and
severities. A time range must be specified as a min/max unix timestamp as well
as the number of alerts to be retrieved.

#### Example Input Request

```
{
  "chains": [
    "chain_name_51383ec9-b49e-4d03-8068-d60f5f3c9285",
    "GENERAL"
  ],
  "severities": [
    "INFO",
    "WARNING",
    "CRITICAL",
    "ERROR"
  ],
  "sources": [
    "system_2a8b23ee-cab6-439c-85ca-d2ba5a45c934",
    "repo_fc4dfda7-2e97-433d-98ba-8af626a989b0",
    "system_5330c562-368b-4192-bbaf-db6638307783",
    "system_d2a0a05e-c0ec-4b39-a101-d3cb5f47bc03",
    "repo_4ca781b6-154e-4bd0-8418-0c5debc07e54"
  ],
  "minTimestamp": 0,
  "maxTimestamp": 2625677273,
  "noOfAlerts": 1000
}
```

#### Example Output Response

```
{
  "result": {
    "alerts": [
      {
        "origin": "system_2a8b23ee-cab6-439c-85ca-d2ba5a45c934",
        "alert_name": "SystemRAMUsageIncreasedAboveThresholdAlert",
        "severity": "CRITICAL",
        "message": "arbitrum system RAM usage INCREASED above CRITICAL Threshold. Current value: 57.09%.",
        "metric": "system_ram_usage",
        "timestamp": 1625828481.76716
      },
      {
        "origin": "system_2a8b23ee-cab6-439c-85ca-d2ba5a45c934",
        "alert_name": "SystemRAMUsageIncreasedAboveThresholdAlert",
        "severity": "CRITICAL",
        "message": "arbitrum system RAM usage INCREASED above CRITICAL Threshold. Current value: 57.09%.",
        "metric": "system_ram_usage",
        "timestamp": 1625828181.168519
      },
      {
        "origin": "system_2a8b23ee-cab6-439c-85ca-d2ba5a45c934",
        "alert_name": "SystemRAMUsageIncreasedAboveThresholdAlert",
        "severity": "CRITICAL",
        "message": "arbitrum system RAM usage INCREASED above CRITICAL Threshold. Current value: 57.08%.",
        "metric": "system_ram_usage",
        "timestamp": 1625827880.603278
      },
      {
        "origin": "system_2a8b23ee-cab6-439c-85ca-d2ba5a45c934",
        "alert_name": "SystemRAMUsageIncreasedAboveThresholdAlert",
        "severity": "CRITICAL",
        "message": "arbitrum system RAM usage INCREASED above CRITICAL Threshold. Current value: 57.05%.",
        "metric": "system_ram_usage",
        "timestamp": 1625827579.997943
      }
    ]
  }
}
```

### `server/mongo/metrics`

Retrieves a list of metrics sorted by time for the requested chains and sources.
A time range must be specified as a min/max unix timestamp as well as the number
of metrics per source to be retrieved.

#### Example Input Request

```
{
  "chains": [
    "chain_name_51383ec9-b49e-4d03-8068-d60f5f3c9285",
    "GENERAL"
  ],
  "sources": [
    "system_2a8b23ee-cab6-439c-85ca-d2ba5a45c934",
    "system_5330c562-368b-4192-bbaf-db6638307783",
    "system_d2a0a05e-c0ec-4b39-a101-d3cb5f47bc03"
],
  "minTimestamp": 0,
  "maxTimestamp": 2625742916,
  "noOfMetricsPerSource": 1
}
```

#### Example Output Response

```
{
  "result": {
    "metrics": {
      "system_2a8b23ee-cab6-439c-85ca-d2ba5a45c934": [
        {
          "process_cpu_seconds_total": "2049.28",
          "process_memory_usage": "0.0",
          "virtual_memory_usage": "735047680.0",
          "open_file_descriptors": "0.9765625",
          "system_cpu_usage": "0.54",
          "system_ram_usage": "53.66",
          "system_storage_usage": "58.5",
          "network_transmit_bytes_per_second": "None",
          "network_receive_bytes_per_second": "None",
          "network_receive_bytes_total": "4286174546.0",
          "network_transmit_bytes_total": "6271111043.0",
          "disk_io_time_seconds_total": "2603.228",
          "disk_io_time_seconds_in_interval": "None",
          "went_down_at": "None",
          "timestamp": 1625657117.224105
        }
      ],
      "system_5330c562-368b-4192-bbaf-db6638307783": [
        {
          "process_cpu_seconds_total": "45869.4",
          "process_memory_usage": "0.0",
          "virtual_memory_usage": "736030720.0",
          "open_file_descriptors": "0.9765625",
          "system_cpu_usage": "38.22",
          "system_ram_usage": "81.08",
          "system_storage_usage": "81.75",
          "network_transmit_bytes_per_second": "None",
          "network_receive_bytes_per_second": "None",
          "network_receive_bytes_total": "3732028217137.0",
          "network_transmit_bytes_total": "6677238313186.0",
          "disk_io_time_seconds_total": "446498.488",
          "disk_io_time_seconds_in_interval": "None",
          "went_down_at": "None",
          "timestamp": 1625657117.331306
        }
      ],
      "system_d2a0a05e-c0ec-4b39-a101-d3cb5f47bc03": [
        {
          "process_cpu_seconds_total": "15404.88",
          "process_memory_usage": "0.0",
          "virtual_memory_usage": "736096256.0",
          "open_file_descriptors": "0.9765625",
          "system_cpu_usage": "4.22",
          "system_ram_usage": "26.94",
          "system_storage_usage": "10.76",
          "network_transmit_bytes_per_second": "None",
          "network_receive_bytes_per_second": "None",
          "network_receive_bytes_total": "2620273043093.0",
          "network_transmit_bytes_total": "2666574158151.0",
          "disk_io_time_seconds_total": "38054.568",
          "disk_io_time_seconds_in_interval": "None",
          "went_down_at": "None",
          "timestamp": 1625657117.230397
        }
      ]
    }
  }
}
```

### `/server/redis/alertsOverview`

Returns an overview of the current state of alerts of the chains for the
requested sources.

#### Example Input Request

```
{
  "parentIds": {
    "chain_name_51383ec9-b49e-4d03-8068-d60f5f3c9285": {
      "include_chain_sourced_alerts": true,
      "systems": ["system_5330c562-368b-4192-bbaf-db6638307783", "system_d2a0a05e-c0ec-4b39-a101-d3cb5f47bc03"],
      "nodes: ["node_9b7dfa8b-5cd8-47cb-b0ac-e8440c4038a9"],
      "github_repos": ["repo_4ca781b6-154e-4bd0-8418-0c5debc07e54"],
      "dockerhub_repos": ["docker_4a9072d6-4cad-44e0-99dd-334333f86390"]
    },
    "GENERAL": {
      "include_chain_sourced_alerts": false,
      "systems": ["system_2a8b23ee-cab6-439c-85ca-d2ba5a45c934"],
      "nodes: ["node_d9acff91-e435-4be9-bc6e-927ee5f0f8c6"],
      "github_repos": ["repo_fc4dfda7-2e97-433d-98ba-8af626a989b0"],
      "dockerhub_repos": ["docker_2c61ce5b-c1c7-429d-a2a4-5700ecdd4413"]
    }
  }
}
```

#### Example Output Response

```
{
  "result": {
    "chain_name_51383ec9-b49e-4d03-8068-d60f5f3c9285": {
      "info": 16,
      "critical": 0,
      "warning": 0,
      "error": 0,
      "problems": {},
      "releases": {}
    },
    "GENERAL": {
      "info": 9,
      "critical": 0,
      "warning": 0,
      "error": 0,
      "problems": {},
      "releases": {}
    }
  }
}
```

### `server/redis/metrics`

Returns the metrics of the data sources being monitored per chain, per data
source. The resulting metrics will be returned by redis key and the value.

#### Example Input Request

```
{
  "parentIds": {
    "chain_name_51383ec9-b49e-4d03-8068-d60f5f3c9285": {
      "systems": ["system_5330c562-368b-4192-bbaf-db6638307783", "system_d2a0a05e-c0ec-4b39-a101-d3cb5f47bc03"],
      "repos": ["repo_4ca781b6-154e-4bd0-8418-0c5debc07e54"]
    },
    "GENERAL": {
      "systems": ["system_2a8b23ee-cab6-439c-85ca-d2ba5a45c934"],
      "repos": ["repo_fc4dfda7-2e97-433d-98ba-8af626a989b0"]
    }
  }
}
```

#### Example Output Response

```
{
  "result": {
    "chain_name_51383ec9-b49e-4d03-8068-d60f5f3c9285": {
      "system": {
        "system_5330c562-368b-4192-bbaf-db6638307783": {
          "s1": "540.24",
          "s2": "0.01",
          "s3": "735047680.0",
          "s4": "0.9765625",
          "s5": "21.73",
          "s6": "81.7",
          "s7": "55.36",
          "s8": "3545659.7070639227",
          "s9": "2028389.0889695366",
          "s10": "207385949202.0",
          "s11": "355206103227.0",
          "s12": "5202.124",
          "s13": "4.960000000000036",
          "s14": "1625828022.131259",
          "s15": "None"
        },
        "system_d2a0a05e-c0ec-4b39-a101-d3cb5f47bc03": {
          "s1": "16077.55",
          "s2": "0.0",
          "s3": "736096256.0",
          "s4": "0.9765625",
          "s5": "4.28",
          "s6": "31.98",
          "s7": "11.9",
          "s8": "2552204.899412914",
          "s9": "1674467.1727744895",
          "s10": "2730052481739.0",
          "s11": "2779064873005.0",
          "s12": "39321.06",
          "s13": "2.4839999999967404",
          "s14": "1625828062.335905",
          "s15": "None"
          }
        },
        "github": {
          "repo_4ca781b6-154e-4bd0-8418-0c5debc07e54": {
            "gh1": "30",
            "gh2": "1625824497.820458"
          }
        }
    },
    "GENERAL": {
      "system": {
        "system_2a8b23ee-cab6-439c-85ca-d2ba5a45c934": {
          "s1": "2358.11",
          "s2": "0.0",
          "s3": "735047680.0",
          "s4": "0.9765625",
          "s5": "0.54",
          "s6": "57.08",
          "s7": "59.23",
          "s8": "4640.324918884027",
          "s9": "3022.6607601624273",
          "s10": "5000997415.0",
          "s11": "7349538544.0",
          "s12": "3041.3999999999996",
          "s13": "0.2719999999999345",
          "s14": "1625828060.940986",
          "s15": "None"
        }
      },
      "github": {
        "repo_fc4dfda7-2e97-433d-98ba-8af626a989b0": {
          "gh1": "2",
          "gh2": "1625824496.731641"
        }
      }
    }
  }
}
```
