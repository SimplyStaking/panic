import { RedisClientNotInitialised } from "../../src/constant/errors";
import {
    addPostfixToKeys,
    addPrefixToKeys,
    alertKeysClNodePrefix,
    alertKeysCosmosNodePrefix,
    alertKeysDockerHubPrefix,
    alertKeysEvmNodePrefix,
    alertKeysGitHubPrefix,
    alertKeysSubstrateNodePrefix,
    alertKeysSystemPrefix,
    getAlertKeysDockerHubRepo,
    getAlertKeysGitHubRepo,
    getAlertKeysNode,
    getAlertKeysSystem,
    getChainKeys,
    getChainlinkNodeKeys,
    getComponentKeys,
    getGitHubKeys,
    getRedisHashes,
    getSystemKeys,
    getUniqueKeys,
    RedisInterface
} from "../../src/server/redis";
import {
    AlertKeysDockerHubRepo,
    AlertKeysGitHubRepo,
    AlertKeysNode,
    AlertKeysSystem,
    ChainKeys,
    ChainlinkNodeKeys,
    ComponentKeys,
    GitHubKeys,
    RedisHashes,
    RedisKeys,
    SystemKeys,
    UniqueKeys
} from "../../src/server/types";

describe('getRedisHashes', () => {
    it('Should return redis hashes', () => {
        const expectedRet: RedisHashes = { parent: 'hash_p1' };
        const ret: any = getRedisHashes();
        expect(ret).toEqual(expectedRet);
    });
});

describe('getUniqueKeys', () => {
    it('Should return unique keys', () => {
        const expectedRet: UniqueKeys = { mute: 'a1' };
        const ret: any = getUniqueKeys();
        expect(ret).toEqual(expectedRet);
    });
});

describe('getSystemKeys', () => {
    it('Should return system keys', () => {
        const expectedRet: SystemKeys = {
            process_cpu_seconds_total: 's1',
            process_memory_usage: 's2',
            virtual_memory_usage: 's3',
            open_file_descriptors: 's4',
            system_cpu_usage: 's5',
            system_ram_usage: 's6',
            system_storage_usage: 's7',
            network_transmit_bytes_per_second: 's8',
            network_receive_bytes_per_second: 's9',
            network_receive_bytes_total: 's10',
            network_transmit_bytes_total: 's11',
            disk_io_time_seconds_total: 's12',
            disk_io_time_seconds_in_interval: 's13',
            last_monitored: 's14',
            system_went_down_at: 's15',
        };
        const ret: any = getSystemKeys();
        expect(ret).toEqual(expectedRet);
    });
});

describe('getGitHubKeys', () => {
    it('Should return github keys', () => {
        const expectedRet: GitHubKeys = {
            no_of_releases: 'gh1',
            last_monitored: 'gh2',
        };
        const ret: any = getGitHubKeys();
        expect(ret).toEqual(expectedRet);
    });
});

describe('getChainlinkNodeKeys', () => {
    it('Should return chainlink node keys', () => {
        const expectedRet: ChainlinkNodeKeys = {
            current_height: 'cl1',
            total_block_headers_received: 'cl2',
            max_pending_tx_delay: 'cl3',
            process_start_time_seconds: 'cl4',
            total_gas_bumps: 'cl5',
            total_gas_bumps_exceeds_limit: 'cl6',
            no_of_unconfirmed_txs: 'cl7',
            total_errored_job_runs: 'cl8',
            current_gas_price_info: 'cl9',
            balance_info: 'cl10',
            went_down_at_prometheus: 'cl11',
            last_prometheus_source_used: 'cl12',
            last_monitored_prometheus: 'cl13',
        };
        const ret: any = getChainlinkNodeKeys();
        expect(ret).toEqual(expectedRet);
    });
});

describe('getComponentKeys', () => {
    it('Should return component keys', () => {
        const expectedRet: ComponentKeys = {
            heartbeat: 'c1'
        };
        const ret: any = getComponentKeys();
        expect(ret).toEqual(expectedRet);
    });
});

describe('getChainKeys', () => {
    it('Should return chain keys', () => {
        const expectedRet: ChainKeys = {
            mute_alerts: 'ch1'
        };
        const ret: any = getChainKeys();
        expect(ret).toEqual(expectedRet);
    });
});

describe('getAlertKeysSystem', () => {
    it('Should return alert system keys', () => {
        const expectedRet: AlertKeysSystem = {
            open_file_descriptors: `${alertKeysSystemPrefix}1`,
            system_cpu_usage: `${alertKeysSystemPrefix}2`,
            system_storage_usage: `${alertKeysSystemPrefix}3`,
            system_ram_usage: `${alertKeysSystemPrefix}4`,
            system_is_down: `${alertKeysSystemPrefix}5`,
            metric_not_found: `${alertKeysSystemPrefix}6`,
            invalid_url: `${alertKeysSystemPrefix}7`,
        };
        const ret: any = getAlertKeysSystem();
        expect(ret).toEqual(expectedRet);
    });
});

describe('getAlertKeysNode', () => {
    it('Should return alert chainlink node keys', () => {
        const expectedRet: AlertKeysNode = {
            cl_head_tracker_current_head: `${alertKeysClNodePrefix}1`,
            cl_head_tracker_heads_received_total: `${alertKeysClNodePrefix}2`,
            cl_max_unconfirmed_blocks: `${alertKeysClNodePrefix}3`,
            cl_process_start_time_seconds: `${alertKeysClNodePrefix}4`,
            cl_tx_manager_gas_bump_exceeds_limit_total: `${alertKeysClNodePrefix}5`,
            cl_unconfirmed_transactions: `${alertKeysClNodePrefix}6`,
            cl_run_status_update_total: `${alertKeysClNodePrefix}7`,
            cl_balance_amount: `${alertKeysClNodePrefix}8`,
            cl_balance_amount_increase: `${alertKeysClNodePrefix}9`,
            cl_invalid_url: `${alertKeysClNodePrefix}10`,
            cl_metric_not_found: `${alertKeysClNodePrefix}11`,
            cl_node_is_down: `${alertKeysClNodePrefix}12`,
            cl_prometheus_is_down: `${alertKeysClNodePrefix}13`,
            evm_node_is_down: `${alertKeysEvmNodePrefix}1`,
            evm_block_syncing_block_height_difference: `${alertKeysEvmNodePrefix}2`,
            evm_block_syncing_no_change_in_block_height: `${alertKeysEvmNodePrefix}3`,
            evm_invalid_url: `${alertKeysEvmNodePrefix}4`,
            cosmos_node_is_down: `${alertKeysCosmosNodePrefix}1`,
            cosmos_node_slashed: `${alertKeysCosmosNodePrefix}2`,
            cosmos_node_syncing: `${alertKeysCosmosNodePrefix}3`,
            cosmos_node_active: `${alertKeysCosmosNodePrefix}4`,
            cosmos_node_jailed: `${alertKeysCosmosNodePrefix}5`,
            cosmos_node_blocks_missed: `${alertKeysCosmosNodePrefix}6`,
            cosmos_node_change_in_height: `${alertKeysCosmosNodePrefix}7`,
            cosmos_node_height_difference: `${alertKeysCosmosNodePrefix}8`,
            cosmos_node_prometheus_url_invalid: `${alertKeysCosmosNodePrefix}9`,
            cosmos_node_cosmos_rest_url_invalid: `${alertKeysCosmosNodePrefix}10`,
            cosmos_node_tendermint_rpc_url_invalid: `${alertKeysCosmosNodePrefix}11`,
            cosmos_node_prometheus_is_down: `${alertKeysCosmosNodePrefix}12`,
            cosmos_node_cosmos_rest_is_down: `${alertKeysCosmosNodePrefix}13`,
            cosmos_node_tendermint_rpc_is_down: `${alertKeysCosmosNodePrefix}14`,
            cosmos_node_no_synced_cosmos_rest_source: `${alertKeysCosmosNodePrefix}15`,
            cosmos_node_no_synced_tendermint_rpc_source: `${alertKeysCosmosNodePrefix}16`,
            cosmos_node_cosmos_rest_data_not_obtained: `${alertKeysCosmosNodePrefix}17`,
            cosmos_node_tendermint_rpc_data_not_obtained: `${alertKeysCosmosNodePrefix}18`,
            cosmos_node_metric_not_found: `${alertKeysCosmosNodePrefix}19`,
            substrate_node_is_down: `${alertKeysSubstrateNodePrefix}1`,
            substrate_node_change_in_best_block_height: `${alertKeysSubstrateNodePrefix}2`,
            substrate_node_change_in_finalized_block_height: `${alertKeysSubstrateNodePrefix}3`,
            substrate_node_syncing: `${alertKeysSubstrateNodePrefix}4`,
            substrate_node_active: `${alertKeysSubstrateNodePrefix}5`,
            substrate_node_disabled: `${alertKeysSubstrateNodePrefix}6`,
            substrate_node_elected: `${alertKeysSubstrateNodePrefix}7`,
            substrate_node_bonded_amount_changed: `${alertKeysSubstrateNodePrefix}8`,
            substrate_node_controller_address_change: `${alertKeysSubstrateNodePrefix}9`,
            substrate_node_no_synced_substrate_websocket_source: `${alertKeysSubstrateNodePrefix}10`,
            substrate_node_substrate_websocket_data_not_obtained: `${alertKeysSubstrateNodePrefix}11`,
            substrate_node_substrate_api_not_reachable: `${alertKeysSubstrateNodePrefix}12`,
            substrate_node_no_heartbeat_and_block_authored_yet: `${alertKeysSubstrateNodePrefix}13`,
            substrate_node_offline: `${alertKeysSubstrateNodePrefix}14`,
            substrate_node_slashed: `${alertKeysSubstrateNodePrefix}15`,
            substrate_node_payout_not_claimed: `${alertKeysSubstrateNodePrefix}16`,
        };
        const ret: any = getAlertKeysNode();
        expect(ret).toEqual(expectedRet);
    });
});

describe('getAlertKeysGitHubRepo', () => {
    it('Should return alert github repo keys', () => {
        const expectedRet: AlertKeysGitHubRepo = {
            github_release: `${alertKeysGitHubPrefix}1`,
            github_cannot_access: `${alertKeysGitHubPrefix}2`,
            github_api_call_error: `${alertKeysGitHubPrefix}3`,
        };
        const ret: any = getAlertKeysGitHubRepo();
        expect(ret).toEqual(expectedRet);
    });
});

describe('getAlertKeysDockerHubRepo', () => {
    it('Should return alert dockerhub repo keys', () => {
        const expectedRet: AlertKeysDockerHubRepo = {
            dockerhub_new_tag: `${alertKeysDockerHubPrefix}1`,
            dockerhub_updated_tag: `${alertKeysDockerHubPrefix}2`,
            dockerhub_deleted_tag: `${alertKeysDockerHubPrefix}3`,
            dockerhub_cannot_access: `${alertKeysDockerHubPrefix}4`,
            dockerhub_tags_api_call_error: `${alertKeysDockerHubPrefix}5`,
        };
        const ret: any = getAlertKeysDockerHubRepo();
        expect(ret).toEqual(expectedRet);
    });
});

describe('addPrefixToKeys', () => {
    it('Should return prefixed keys', () => {
        const prefix: string = 'test_';
        const keysObjects: RedisKeys[] = [
            getRedisHashes(), getUniqueKeys(), getGitHubKeys()]
        const keysObjectsResults: RedisKeys[] = [
            { parent: 'test_hash_p1' },
            { mute: 'test_a1' },
            {
                no_of_releases: 'test_gh1',
                last_monitored: 'test_gh2'
            }
        ]

        for (const [i] of keysObjects.entries()) {
            const ret: RedisKeys = addPrefixToKeys(keysObjects[i], prefix)
            expect(ret).toEqual(keysObjectsResults[i]);
        }
    });
});

describe('addPostfixToKeys', () => {
    it('Should return postfixed keys', () => {
        const postfix: string = '_test';
        const keysObjects: RedisKeys[] = [getRedisHashes(), getUniqueKeys(),
        getGitHubKeys()]
        const keysObjectsResults: RedisKeys[] = [
            { parent: 'hash_p1_test' },
            { mute: 'a1_test' },
            {
                no_of_releases: 'gh1_test',
                last_monitored: 'gh2_test'
            }
        ]

        for (const [i] of keysObjects.entries()) {
            const ret: RedisKeys = addPostfixToKeys(keysObjects[i], postfix)
            expect(ret).toEqual(keysObjectsResults[i]);
        }
    });
});

describe('RedisInterface', () => {
    const redisInterface: RedisInterface = new RedisInterface();
    it('client should return undefined if client is not initialised',
        () => {
            const ret = redisInterface.client;
            expect(ret).toBeUndefined();
        })

    it('disconnect should throw error if client is not initialised',
        () => {
            expect(() => {
                redisInterface.disconnect()
            }).toThrowError(new RedisClientNotInitialised());
        })
});
