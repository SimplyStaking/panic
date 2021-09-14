import { BaseChain, Chain } from "../interfaces/chains";
import { apiURL, baseChainsNames } from "./constants";

/**
 * Gets the base chains from the API and populates them with chain information.
 * @returns list of populated base chains.
 */
export async function getMonitorablesInfo(): Promise<BaseChain[]> {
    const monitorablesInfo: Response = await fetch(`${apiURL}redis/monitorablesInfo`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "baseChains": baseChainsNames
            })
        }
    );

    const data: any = await monitorablesInfo.json();
    const baseChains: BaseChain[] = [];

    for (const baseChain in data.result) {
        if (data.result[baseChain]) {
            const currentChains: Chain[] = [];
            let index: number = 0;
            for (const currentChain in data.result[baseChain]) {
                // Systems case.
                const currentSystems: string[] = [];
                for (const system of data.result[baseChain][currentChain].monitored.systems) {
                    currentSystems.push(Object.keys(system)[0]);
                }

                // Repos case.
                const currentRepos: string[] = [];
                for (const type of Object.keys(data.result[baseChain][currentChain].monitored)) {
                    if (type.includes('repo')) {
                        for (const repo of data.result[baseChain][currentChain].monitored[type]) {
                            currentRepos.push(Object.keys(repo)[0]);
                        }
                    }
                }

                currentChains.push({
                    name: currentChain,
                    id: data.result[baseChain][currentChain].parent_id,
                    repos: currentRepos,
                    systems: currentSystems,
                    criticalAlerts: 0,
                    warningAlerts: 0,
                    errorAlerts: 0,
                    totalAlerts: 0,
                    active: index == 0
                });

                index++;
            }

            baseChains.push({
                name: baseChain,
                chains: currentChains
            });
        }
    }

    return baseChains;
}

/**
 * Gets the alerts of all of the chains within each base chain.
 * @param baseChains base chains to be updated.
 * @returns updated chains.
 */
export async function getAllBaseChains(baseChains: BaseChain[]): Promise<BaseChain[]> {
    const updatedBaseChains: BaseChain[] = [];
    for (let baseChain of baseChains) {
        const updatedBaseChain: BaseChain = {
            name: baseChain.name,
            chains: baseChain.chains
        };
        for (let chain of updatedBaseChain.chains) {
            if (chain.active) {
                const result = await getChainAlerts(chain);
                chain = result;
            }
        }
        updatedBaseChains.push(updatedBaseChain);
    }

    return updatedBaseChains;
}

/**
 * Updates the alerts of a given chain while noting whether it changed.
 * @param chain chain to be updated.
 * @returns updated chain and whether it was changed.
 */
async function getChainAlerts(chain: Chain): Promise<Chain> {
    try {
        const data: any = await getAlertsOverview(chain);
        chain.criticalAlerts = data.result[chain.id].critical;
        chain.warningAlerts = data.result[chain.id].warning;
        chain.errorAlerts = data.result[chain.id].error;
        chain.totalAlerts = chain.criticalAlerts + chain.warningAlerts + chain.errorAlerts;

    } catch (error: any) {
        console.error(error);
    }

    return chain;
}

/**
 * Gets the alerts overview of a given chain.
 * @param chain chain to be checked.
 * @returns chain data as JSON.
 */
async function getAlertsOverview(chain: Chain): Promise<any> {
    let chainSources = { parentIds: {} };
    chainSources.parentIds[chain.id] = { systems: [], repos: [] };
    chainSources.parentIds[chain.id].systems = chain.systems;
    chainSources.parentIds[chain.id].repos = chain.repos;

    try {
        const alertsOverview = await fetch(`${apiURL}redis/alertsOverview`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(chainSources)
            });

        return await alertsOverview.json();
    } catch (error: any) {
        console.error(error);
    }
}
