import { BaseChain, Chain } from "../interfaces/chains";
import { apiURL, baseChainsNames } from "./constants";

/**
 * Gets the monitorable information of the base chains from the API.
 * @returns the monitorable information of the base chains as a JSON object.
 */
async function getMonitorablesInfo(): Promise<any> {
    try {
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

        return await monitorablesInfo.json();
    } catch (error: any) {
        console.error(error);
    }
}

/**
 * Gets the alerts overview of a given chain.
 * @param chain chain to be checked.
 * @returns chain data as a JSON object.
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

/**
 * Gets the base chains from the API and formats them with the chain information.
 * @returns list of populated base chains.
 */
export async function getBaseChains(): Promise<BaseChain[]> {
    const data: any = await getMonitorablesInfo();
    const baseChains: BaseChain[] = [];

    for (const baseChain in data.result) {
        if (data.result[baseChain]) {
            const currentChains: Chain[] = [];
            let index: number = 0;
            for (const currentChain in data.result[baseChain]) {
                // Systems case.
                const currentSystems: string[] = [];
                if (data.result[baseChain][currentChain].monitored.systems) {
                    for (const system of data.result[baseChain][currentChain].monitored.systems) {
                        currentSystems.push(Object.keys(system)[0]);
                    }
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
 * Updates the alerts of all of the chains within each base chain.
 * @param baseChains base chains to be updated.
 * @returns updated chains.
 */
export async function updateBaseChains(baseChains: BaseChain[]): Promise<BaseChain[]> {
    const updatedBaseChains: BaseChain[] = [];
    for (const baseChain of baseChains) {
        updatedBaseChains.push({
            name: baseChain.name,
            chains: baseChain.chains
        });
    }

    const newBaseChains: BaseChain[] = await getBaseChains();

    // Add newly added base chains (if any).
    for (const newBaseChain of newBaseChains) {
        const updatedBaseChain: BaseChain = updatedBaseChains.find(baseChain => baseChain.name === newBaseChain.name);
        if (!updatedBaseChain) {
            // Add new base chain.
            updatedBaseChains.push(newBaseChain);
        } else {
            // Check for newly added/removed chains within base chain.
            for (const newChain of newBaseChain.chains) {
                // Add newly added chains (if any).
                if (!updatedBaseChain.chains.find(chain => chain.id === newChain.id)) {
                    newChain.active = false;
                    updatedBaseChain.chains.push(newChain);
                }
            }

            // Remove newly removed chains (if any).
            const removedChains: Chain[] = [];
            for (const updatedChain of updatedBaseChain.chains) {
                if (!newBaseChain.chains.find(chain => chain.id === updatedChain.id)) {
                    removedChains.push(updatedChain);
                }
            }
            for (const removedChain of removedChains) {
                const index = updatedBaseChain.chains.indexOf(removedChain);
                if (index > -1) {
                    updatedBaseChain.chains.splice(index, 1);
                } else {
                    console.error('This should always exist.');
                }
            }
        }
    }

    // Remove newly removed base chains (if any).
    const removedBaseChains: BaseChain[] = [];
    for (const updatedBaseChain of updatedBaseChains) {
        if (!newBaseChains.find(baseChain => baseChain.name === updatedBaseChain.name)) {
            removedBaseChains.push(updatedBaseChain);
        }
    }
    for (const removedBaseChain of removedBaseChains) {
        const index = updatedBaseChains.indexOf(removedBaseChain);
        if (index > -1) {
            updatedBaseChains.splice(index, 1);
        } else {
            console.error('This should always exist.');
        }
    }


    // Populate each active chain within each base chain.
    for (const updatedBaseChain of updatedBaseChains) {
        for (let chain of updatedBaseChain.chains) {
            if (chain.active) {
                const result = await getChainAlerts(chain);
                chain = result;
            }
        }
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
