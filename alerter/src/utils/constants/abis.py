V3 = [
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_link",
                "type": "address"
            },
            {
                "internalType": "uint128",
                "name": "_paymentAmount",
                "type": "uint128"
            },
            {
                "internalType": "uint32",
                "name": "_timeout",
                "type": "uint32"
            },
            {
                "internalType": "address",
                "name": "_validator",
                "type": "address"
            },
            {
                "internalType": "int256",
                "name": "_minSubmissionValue",
                "type": "int256"
            },
            {
                "internalType": "int256",
                "name": "_maxSubmissionValue",
                "type": "int256"
            },
            {
                "internalType": "uint8",
                "name": "_decimals",
                "type": "uint8"
            },
            {
                "internalType": "string",
                "name": "_description",
                "type": "string"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "address",
                "name": "user",
                "type": "address"
            }
        ],
        "name": "AddedAccess",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "int256",
                "name": "current",
                "type": "int256"
            },
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "roundId",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "updatedAt",
                "type": "uint256"
            }
        ],
        "name": "AnswerUpdated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "AvailableFundsUpdated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [],
        "name": "CheckAccessDisabled",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [],
        "name": "CheckAccessEnabled",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "roundId",
                "type": "uint256"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "startedBy",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "startedAt",
                "type": "uint256"
            }
        ],
        "name": "NewRound",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "oracle",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "admin",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "newAdmin",
                "type": "address"
            }
        ],
        "name": "OracleAdminUpdateRequested",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "oracle",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "newAdmin",
                "type": "address"
            }
        ],
        "name": "OracleAdminUpdated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "oracle",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "bool",
                "name": "whitelisted",
                "type": "bool"
            }
        ],
        "name": "OraclePermissionsUpdated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "from",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "to",
                "type": "address"
            }
        ],
        "name": "OwnershipTransferRequested",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "from",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "to",
                "type": "address"
            }
        ],
        "name": "OwnershipTransferred",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "address",
                "name": "user",
                "type": "address"
            }
        ],
        "name": "RemovedAccess",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "requester",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "bool",
                "name": "authorized",
                "type": "bool"
            },
            {
                "indexed": False,
                "internalType": "uint32",
                "name": "delay",
                "type": "uint32"
            }
        ],
        "name": "RequesterPermissionsSet",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint128",
                "name": "paymentAmount",
                "type": "uint128"
            },
            {
                "indexed": True,
                "internalType": "uint32",
                "name": "minSubmissionCount",
                "type": "uint32"
            },
            {
                "indexed": True,
                "internalType": "uint32",
                "name": "maxSubmissionCount",
                "type": "uint32"
            },
            {
                "indexed": False,
                "internalType": "uint32",
                "name": "restartDelay",
                "type": "uint32"
            },
            {
                "indexed": False,
                "internalType": "uint32",
                "name": "timeout",
                "type": "uint32"
            }
        ],
        "name": "RoundDetailsUpdated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "int256",
                "name": "submission",
                "type": "int256"
            },
            {
                "indexed": True,
                "internalType": "uint32",
                "name": "round",
                "type": "uint32"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "oracle",
                "type": "address"
            }
        ],
        "name": "SubmissionReceived",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "previous",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "current",
                "type": "address"
            }
        ],
        "name": "ValidatorUpdated",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_oracle",
                "type": "address"
            }
        ],
        "name": "acceptAdmin",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "acceptOwnership",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_user",
                "type": "address"
            }
        ],
        "name": "addAccess",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "allocatedFunds",
        "outputs": [
            {
                "internalType": "uint128",
                "name": "",
                "type": "uint128"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "availableFunds",
        "outputs": [
            {
                "internalType": "uint128",
                "name": "",
                "type": "uint128"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "_removed",
                "type": "address[]"
            },
            {
                "internalType": "address[]",
                "name": "_added",
                "type": "address[]"
            },
            {
                "internalType": "address[]",
                "name": "_addedAdmins",
                "type": "address[]"
            },
            {
                "internalType": "uint32",
                "name": "_minSubmissions",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "_maxSubmissions",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "_restartDelay",
                "type": "uint32"
            }
        ],
        "name": "changeOracles",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "checkEnabled",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [
            {
                "internalType": "uint8",
                "name": "",
                "type": "uint8"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "description",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "disableAccessCheck",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "enableAccessCheck",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_oracle",
                "type": "address"
            }
        ],
        "name": "getAdmin",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "_roundId",
                "type": "uint256"
            }
        ],
        "name": "getAnswer",
        "outputs": [
            {
                "internalType": "int256",
                "name": "",
                "type": "int256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getOracles",
        "outputs": [
            {
                "internalType": "address[]",
                "name": "",
                "type": "address[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint80",
                "name": "_roundId",
                "type": "uint80"
            }
        ],
        "name": "getRoundData",
        "outputs": [
            {
                "internalType": "uint80",
                "name": "roundId",
                "type": "uint80"
            },
            {
                "internalType": "int256",
                "name": "answer",
                "type": "int256"
            },
            {
                "internalType": "uint256",
                "name": "startedAt",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "updatedAt",
                "type": "uint256"
            },
            {
                "internalType": "uint80",
                "name": "answeredInRound",
                "type": "uint80"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "_roundId",
                "type": "uint256"
            }
        ],
        "name": "getTimestamp",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_user",
                "type": "address"
            },
            {
                "internalType": "bytes",
                "name": "_calldata",
                "type": "bytes"
            }
        ],
        "name": "hasAccess",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "latestAnswer",
        "outputs": [
            {
                "internalType": "int256",
                "name": "",
                "type": "int256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "latestRound",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {
                "internalType": "uint80",
                "name": "roundId",
                "type": "uint80"
            },
            {
                "internalType": "int256",
                "name": "answer",
                "type": "int256"
            },
            {
                "internalType": "uint256",
                "name": "startedAt",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "updatedAt",
                "type": "uint256"
            },
            {
                "internalType": "uint80",
                "name": "answeredInRound",
                "type": "uint80"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "latestTimestamp",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "linkToken",
        "outputs": [
            {
                "internalType": "contract LinkTokenInterface",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "maxSubmissionCount",
        "outputs": [
            {
                "internalType": "uint32",
                "name": "",
                "type": "uint32"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "maxSubmissionValue",
        "outputs": [
            {
                "internalType": "int256",
                "name": "",
                "type": "int256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "minSubmissionCount",
        "outputs": [
            {
                "internalType": "uint32",
                "name": "",
                "type": "uint32"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "minSubmissionValue",
        "outputs": [
            {
                "internalType": "int256",
                "name": "",
                "type": "int256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            },
            {
                "internalType": "bytes",
                "name": "_data",
                "type": "bytes"
            }
        ],
        "name": "onTokenTransfer",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "oracleCount",
        "outputs": [
            {
                "internalType": "uint8",
                "name": "",
                "type": "uint8"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_oracle",
                "type": "address"
            },
            {
                "internalType": "uint32",
                "name": "_queriedRoundId",
                "type": "uint32"
            }
        ],
        "name": "oracleRoundState",
        "outputs": [
            {
                "internalType": "bool",
                "name": "_eligibleToSubmit",
                "type": "bool"
            },
            {
                "internalType": "uint32",
                "name": "_roundId",
                "type": "uint32"
            },
            {
                "internalType": "int256",
                "name": "_latestSubmission",
                "type": "int256"
            },
            {
                "internalType": "uint64",
                "name": "_startedAt",
                "type": "uint64"
            },
            {
                "internalType": "uint64",
                "name": "_timeout",
                "type": "uint64"
            },
            {
                "internalType": "uint128",
                "name": "_availableFunds",
                "type": "uint128"
            },
            {
                "internalType": "uint8",
                "name": "_oracleCount",
                "type": "uint8"
            },
            {
                "internalType": "uint128",
                "name": "_paymentAmount",
                "type": "uint128"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "paymentAmount",
        "outputs": [
            {
                "internalType": "uint128",
                "name": "",
                "type": "uint128"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_user",
                "type": "address"
            }
        ],
        "name": "removeAccess",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "requestNewRound",
        "outputs": [
            {
                "internalType": "uint80",
                "name": "",
                "type": "uint80"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "restartDelay",
        "outputs": [
            {
                "internalType": "uint32",
                "name": "",
                "type": "uint32"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_requester",
                "type": "address"
            },
            {
                "internalType": "bool",
                "name": "_authorized",
                "type": "bool"
            },
            {
                "internalType": "uint32",
                "name": "_delay",
                "type": "uint32"
            }
        ],
        "name": "setRequesterPermissions",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_newValidator",
                "type": "address"
            }
        ],
        "name": "setValidator",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "_roundId",
                "type": "uint256"
            },
            {
                "internalType": "int256",
                "name": "_submission",
                "type": "int256"
            }
        ],
        "name": "submit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "timeout",
        "outputs": [
            {
                "internalType": "uint32",
                "name": "",
                "type": "uint32"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_oracle",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "_newAdmin",
                "type": "address"
            }
        ],
        "name": "transferAdmin",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_to",
                "type": "address"
            }
        ],
        "name": "transferOwnership",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "updateAvailableFunds",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint128",
                "name": "_paymentAmount",
                "type": "uint128"
            },
            {
                "internalType": "uint32",
                "name": "_minSubmissions",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "_maxSubmissions",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "_restartDelay",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "_timeout",
                "type": "uint32"
            }
        ],
        "name": "updateFutureRounds",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "validator",
        "outputs": [
            {
                "internalType": "contract AggregatorValidatorInterface",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "version",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_recipient",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "_amount",
                "type": "uint256"
            }
        ],
        "name": "withdrawFunds",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_oracle",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "_recipient",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "_amount",
                "type": "uint256"
            }
        ],
        "name": "withdrawPayment",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_oracle",
                "type": "address"
            }
        ],
        "name": "withdrawablePayment",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

V4 = [
    {
        "inputs": [
            {
                "internalType": "uint32",
                "name": "_maximumGasPrice",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "_reasonableGasPrice",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "_microLinkPerEth",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "_linkGweiPerObservation",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "_linkGweiPerTransmission",
                "type": "uint32"
            },
            {
                "internalType": "address",
                "name": "_link",
                "type": "address"
            },
            {
                "internalType": "int192",
                "name": "_minAnswer",
                "type": "int192"
            },
            {
                "internalType": "int192",
                "name": "_maxAnswer",
                "type": "int192"
            },
            {
                "internalType": "contract AccessControllerInterface",
                "name": "_billingAccessController",
                "type": "address"
            },
            {
                "internalType": "contract AccessControllerInterface",
                "name": "_requesterAccessController",
                "type": "address"
            },
            {
                "internalType": "uint8",
                "name": "_decimals",
                "type": "uint8"
            },
            {
                "internalType": "string",
                "name": "description",
                "type": "string"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "address",
                "name": "user",
                "type": "address"
            }
        ],
        "name": "AddedAccess",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "int256",
                "name": "current",
                "type": "int256"
            },
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "roundId",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "updatedAt",
                "type": "uint256"
            }
        ],
        "name": "AnswerUpdated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "contract AccessControllerInterface",
                "name": "old",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "contract AccessControllerInterface",
                "name": "current",
                "type": "address"
            }
        ],
        "name": "BillingAccessControllerSet",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "uint32",
                "name": "maximumGasPrice",
                "type": "uint32"
            },
            {
                "indexed": False,
                "internalType": "uint32",
                "name": "reasonableGasPrice",
                "type": "uint32"
            },
            {
                "indexed": False,
                "internalType": "uint32",
                "name": "microLinkPerEth",
                "type": "uint32"
            },
            {
                "indexed": False,
                "internalType": "uint32",
                "name": "linkGweiPerObservation",
                "type": "uint32"
            },
            {
                "indexed": False,
                "internalType": "uint32",
                "name": "linkGweiPerTransmission",
                "type": "uint32"
            }
        ],
        "name": "BillingSet",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [],
        "name": "CheckAccessDisabled",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [],
        "name": "CheckAccessEnabled",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "uint32",
                "name": "previousConfigBlockNumber",
                "type": "uint32"
            },
            {
                "indexed": False,
                "internalType": "uint64",
                "name": "configCount",
                "type": "uint64"
            },
            {
                "indexed": False,
                "internalType": "address[]",
                "name": "signers",
                "type": "address[]"
            },
            {
                "indexed": False,
                "internalType": "address[]",
                "name": "transmitters",
                "type": "address[]"
            },
            {
                "indexed": False,
                "internalType": "uint8",
                "name": "threshold",
                "type": "uint8"
            },
            {
                "indexed": False,
                "internalType": "uint64",
                "name": "encodedConfigVersion",
                "type": "uint64"
            },
            {
                "indexed": False,
                "internalType": "bytes",
                "name": "encoded",
                "type": "bytes"
            }
        ],
        "name": "ConfigSet",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "roundId",
                "type": "uint256"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "startedBy",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "startedAt",
                "type": "uint256"
            }
        ],
        "name": "NewRound",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint32",
                "name": "aggregatorRoundId",
                "type": "uint32"
            },
            {
                "indexed": False,
                "internalType": "int192",
                "name": "answer",
                "type": "int192"
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "transmitter",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "int192[]",
                "name": "observations",
                "type": "int192[]"
            },
            {
                "indexed": False,
                "internalType": "bytes",
                "name": "observers",
                "type": "bytes"
            },
            {
                "indexed": False,
                "internalType": "bytes32",
                "name": "rawReportContext",
                "type": "bytes32"
            }
        ],
        "name": "NewTransmission",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "address",
                "name": "transmitter",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "payee",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "OraclePaid",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "from",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "to",
                "type": "address"
            }
        ],
        "name": "OwnershipTransferRequested",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "from",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "to",
                "type": "address"
            }
        ],
        "name": "OwnershipTransferred",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "transmitter",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "current",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "proposed",
                "type": "address"
            }
        ],
        "name": "PayeeshipTransferRequested",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "transmitter",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "previous",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "current",
                "type": "address"
            }
        ],
        "name": "PayeeshipTransferred",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "address",
                "name": "user",
                "type": "address"
            }
        ],
        "name": "RemovedAccess",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "contract AccessControllerInterface",
                "name": "old",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "contract AccessControllerInterface",
                "name": "current",
                "type": "address"
            }
        ],
        "name": "RequesterAccessControllerSet",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "requester",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "bytes16",
                "name": "configDigest",
                "type": "bytes16"
            },
            {
                "indexed": False,
                "internalType": "uint32",
                "name": "epoch",
                "type": "uint32"
            },
            {
                "indexed": False,
                "internalType": "uint8",
                "name": "round",
                "type": "uint8"
            }
        ],
        "name": "RoundRequested",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "contract AggregatorValidatorInterface",
                "name": "previousValidator",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint32",
                "name": "previousGasLimit",
                "type": "uint32"
            },
            {
                "indexed": True,
                "internalType": "contract AggregatorValidatorInterface",
                "name": "currentValidator",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint32",
                "name": "currentGasLimit",
                "type": "uint32"
            }
        ],
        "name": "ValidatorConfigSet",
        "type": "event"
    },
    {
        "inputs": [],
        "name": "LINK",
        "outputs": [
            {
                "internalType": "contract LinkTokenInterface",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "acceptOwnership",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_transmitter",
                "type": "address"
            }
        ],
        "name": "acceptPayeeship",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_user",
                "type": "address"
            }
        ],
        "name": "addAccess",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "billingAccessController",
        "outputs": [
            {
                "internalType": "contract AccessControllerInterface",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "checkEnabled",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [
            {
                "internalType": "uint8",
                "name": "",
                "type": "uint8"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "description",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "disableAccessCheck",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "enableAccessCheck",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "_roundId",
                "type": "uint256"
            }
        ],
        "name": "getAnswer",
        "outputs": [
            {
                "internalType": "int256",
                "name": "",
                "type": "int256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getBilling",
        "outputs": [
            {
                "internalType": "uint32",
                "name": "maximumGasPrice",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "reasonableGasPrice",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "microLinkPerEth",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "linkGweiPerObservation",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "linkGweiPerTransmission",
                "type": "uint32"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint80",
                "name": "_roundId",
                "type": "uint80"
            }
        ],
        "name": "getRoundData",
        "outputs": [
            {
                "internalType": "uint80",
                "name": "roundId",
                "type": "uint80"
            },
            {
                "internalType": "int256",
                "name": "answer",
                "type": "int256"
            },
            {
                "internalType": "uint256",
                "name": "startedAt",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "updatedAt",
                "type": "uint256"
            },
            {
                "internalType": "uint80",
                "name": "answeredInRound",
                "type": "uint80"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "_roundId",
                "type": "uint256"
            }
        ],
        "name": "getTimestamp",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_user",
                "type": "address"
            },
            {
                "internalType": "bytes",
                "name": "_calldata",
                "type": "bytes"
            }
        ],
        "name": "hasAccess",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "latestAnswer",
        "outputs": [
            {
                "internalType": "int256",
                "name": "",
                "type": "int256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "latestConfigDetails",
        "outputs": [
            {
                "internalType": "uint32",
                "name": "configCount",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "blockNumber",
                "type": "uint32"
            },
            {
                "internalType": "bytes16",
                "name": "configDigest",
                "type": "bytes16"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "latestRound",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {
                "internalType": "uint80",
                "name": "roundId",
                "type": "uint80"
            },
            {
                "internalType": "int256",
                "name": "answer",
                "type": "int256"
            },
            {
                "internalType": "uint256",
                "name": "startedAt",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "updatedAt",
                "type": "uint256"
            },
            {
                "internalType": "uint80",
                "name": "answeredInRound",
                "type": "uint80"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "latestTimestamp",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "latestTransmissionDetails",
        "outputs": [
            {
                "internalType": "bytes16",
                "name": "configDigest",
                "type": "bytes16"
            },
            {
                "internalType": "uint32",
                "name": "epoch",
                "type": "uint32"
            },
            {
                "internalType": "uint8",
                "name": "round",
                "type": "uint8"
            },
            {
                "internalType": "int192",
                "name": "latestAnswer",
                "type": "int192"
            },
            {
                "internalType": "uint64",
                "name": "latestTimestamp",
                "type": "uint64"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "linkAvailableForPayment",
        "outputs": [
            {
                "internalType": "int256",
                "name": "availableBalance",
                "type": "int256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "maxAnswer",
        "outputs": [
            {
                "internalType": "int192",
                "name": "",
                "type": "int192"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "minAnswer",
        "outputs": [
            {
                "internalType": "int192",
                "name": "",
                "type": "int192"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_signerOrTransmitter",
                "type": "address"
            }
        ],
        "name": "oracleObservationCount",
        "outputs": [
            {
                "internalType": "uint16",
                "name": "",
                "type": "uint16"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_transmitter",
                "type": "address"
            }
        ],
        "name": "owedPayment",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [
            {
                "internalType": "address payable",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_user",
                "type": "address"
            }
        ],
        "name": "removeAccess",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "requestNewRound",
        "outputs": [
            {
                "internalType": "uint80",
                "name": "",
                "type": "uint80"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "requesterAccessController",
        "outputs": [
            {
                "internalType": "contract AccessControllerInterface",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint32",
                "name": "_maximumGasPrice",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "_reasonableGasPrice",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "_microLinkPerEth",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "_linkGweiPerObservation",
                "type": "uint32"
            },
            {
                "internalType": "uint32",
                "name": "_linkGweiPerTransmission",
                "type": "uint32"
            }
        ],
        "name": "setBilling",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "contract AccessControllerInterface",
                "name": "_billingAccessController",
                "type": "address"
            }
        ],
        "name": "setBillingAccessController",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "_signers",
                "type": "address[]"
            },
            {
                "internalType": "address[]",
                "name": "_transmitters",
                "type": "address[]"
            },
            {
                "internalType": "uint8",
                "name": "_threshold",
                "type": "uint8"
            },
            {
                "internalType": "uint64",
                "name": "_encodedConfigVersion",
                "type": "uint64"
            },
            {
                "internalType": "bytes",
                "name": "_encoded",
                "type": "bytes"
            }
        ],
        "name": "setConfig",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address[]",
                "name": "_transmitters",
                "type": "address[]"
            },
            {
                "internalType": "address[]",
                "name": "_payees",
                "type": "address[]"
            }
        ],
        "name": "setPayees",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "contract AccessControllerInterface",
                "name": "_requesterAccessController",
                "type": "address"
            }
        ],
        "name": "setRequesterAccessController",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "contract AggregatorValidatorInterface",
                "name": "_newValidator",
                "type": "address"
            },
            {
                "internalType": "uint32",
                "name": "_newGasLimit",
                "type": "uint32"
            }
        ],
        "name": "setValidatorConfig",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_to",
                "type": "address"
            }
        ],
        "name": "transferOwnership",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_transmitter",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "_proposed",
                "type": "address"
            }
        ],
        "name": "transferPayeeship",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "bytes",
                "name": "_report",
                "type": "bytes"
            },
            {
                "internalType": "bytes32[]",
                "name": "_rs",
                "type": "bytes32[]"
            },
            {
                "internalType": "bytes32[]",
                "name": "_ss",
                "type": "bytes32[]"
            },
            {
                "internalType": "bytes32",
                "name": "_rawVs",
                "type": "bytes32"
            }
        ],
        "name": "transmit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "transmitters",
        "outputs": [
            {
                "internalType": "address[]",
                "name": "",
                "type": "address[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "typeAndVersion",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "stateMutability": "pure",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "validatorConfig",
        "outputs": [
            {
                "internalType": "contract AggregatorValidatorInterface",
                "name": "validator",
                "type": "address"
            },
            {
                "internalType": "uint32",
                "name": "gasLimit",
                "type": "uint32"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "version",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_recipient",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "_amount",
                "type": "uint256"
            }
        ],
        "name": "withdrawFunds",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_transmitter",
                "type": "address"
            }
        ],
        "name": "withdrawPayment",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]
