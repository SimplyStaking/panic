import { BaseChain, Chain } from "../interfaces/chains";
import { apiURL, baseChainsNames } from "./constants";
import { AlertsOverviewAPI } from "./alertsOverview";

export const ChainsAPI = {
    // panic-dashboard-overview
    getBaseChains: getBaseChains,
    updateBaseChains: updateBaseChains,
    updateActiveChainsInBaseChain: updateActiveChainsInBaseChain,
    // panic-alerts-overview
    getChains: getChains,
    updateChains: updateChains,
    activeChainsSources: activeChainsSources,
    updateActiveChains: updateActiveChains,
    // used in both
    getChainFilterValue: getChainFilterValue
}

/**
 * DASHBOARD OVERVIEW
 * The functions below are used within the panic-dashboard-overview component.
 * The logic within this component consists of having an array of base chains
 * which contain a list of chains. These base chains are then updated with the
 * data as required. The logic below also takes into account when base chains
 * and/or chains are removed or added while PANIC UI is running.
 */

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
        console.log('Error getting monitorables info -', error);
        return { result: {} }
    }
}

/**
 * Gets the base chains from the API and formats them with the chain information.
 * @returns list of populated base chains.
 */
async function getBaseChains(): Promise<BaseChain[]> {
    const data: any = await getMonitorablesInfo();
    const baseChains: BaseChain[] = [];

    for (const baseChain in data.result) {
        if (data.result[baseChain]) {
            const currentChains: Chain[] = [];
            for (const currentChain in data.result[baseChain]) {
                // Skip chain if monitored field does not exist.
                if (!data.result[baseChain][currentChain].monitored) {
                    continue;
                }

                // Get Systems.
                const currentSystems: string[] = getSystems(data.result[baseChain][currentChain].monitored.systems);
                // Get Repos.
                const currentRepos: string[] = getRepos(data.result[baseChain][currentChain].monitored);

                // Skip chain if it does not contain any monitorable sources.
                if (currentSystems.length + currentRepos.length === 0) {
                    continue;
                }

                currentChains.push({
                    name: currentChain,
                    id: data.result[baseChain][currentChain].parent_id,
                    repos: currentRepos,
                    systems: currentSystems,
                    alerts: [],
                    active: true
                });
            }

            // Skip base chain if its chains do not contain any monitorable sources.
            if (currentChains.length == 0) {
                continue;
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
 * Returns a list of system IDs given a systems object.
 * @param systems object retrieved from JSON.
 * @returns list of system IDs.
 */
function getSystems(systems: any): string[] {
    const currentSystems: string[] = [];

    if (systems) {
        for (const system of systems) {
            currentSystems.push(Object.keys(system)[0]);
        }
    }

    return currentSystems;
}

/**
 * Returns a list of repo IDs given a repos object.
 * @param repos object retrieved from JSON.
 * @returns list of repo IDs.
 */
function getRepos(monitored: any): string[] {
    const currentRepos: string[] = [];

    for (const type of Object.keys(monitored)) {
        if (type.includes('repo')) {
            for (const repo of monitored[type]) {
                currentRepos.push(Object.keys(repo)[0]);
            }
        }
    }
    return currentRepos;
}

/**
 * Updates base chains and the alerts within.
 * @param baseChains base chains to be updated.
 * @returns updated base chains.
 */
async function updateBaseChains(baseChains: BaseChain[]): Promise<BaseChain[]> {
    const newBaseChains: BaseChain[] = await getBaseChains();

    // Add newly added base chains (if any).
    let updatedBaseChains: BaseChain[] = addNewlyAddedBaseChains(baseChains, newBaseChains);

    // Remove newly removed base chains (if any).
    updatedBaseChains = removeNewlyRemovedBaseChains(updatedBaseChains, newBaseChains);

    // Update base chains with redis alerts.
    updatedBaseChains = await updateBaseChainsWithAlerts(updatedBaseChains);

    return updatedBaseChains;
}

/**
 * Adds newly added base chains while also checking newly added/removed chains within.
 * @param updatedBaseChains base chains to be updated.
 * @param newBaseChains new base chains (latest from API).
 * @returns updated base chains.
 */
function addNewlyAddedBaseChains(updatedBaseChains: BaseChain[], newBaseChains: BaseChain[]): BaseChain[] {
    const finalBaseChains: BaseChain[] = [];

    for (let newBaseChain of newBaseChains) {
        const updatedBaseChain: BaseChain = updatedBaseChains.find(baseChain => baseChain.name === newBaseChain.name);
        if (updatedBaseChain) {
            // Create base chain.
            const finalBaseChain: BaseChain = {
                name: updatedBaseChain.name,
                chains: []
            };
            // Check for newly added/removed chains within base chain.
            for (const newChain of newBaseChain.chains) {
                // Add newly added chains (if any).
                if (!updatedBaseChain.chains.find(chain => chain.id === newChain.id)) {
                    newChain.active = false;
                    finalBaseChain.chains.push(newChain);
                }
            }

            // Do not add newly removed chains (if any) / Add common chains only.
            for (const updatedChain of updatedBaseChain.chains) {
                if (newBaseChain.chains.find(chain => chain.id === updatedChain.id)) {
                    finalBaseChain.chains.push(updatedChain);
                }
            }

            // Add base chain.
            finalBaseChains.push(finalBaseChain);
        } else {
            // Add newly added base chain.
            finalBaseChains.push(newBaseChain);
        }
    }

    return finalBaseChains;
}

/**
 * Removes newly removed base chains.
 * @param updatedBaseChains base chains to be updated.
 * @param newBaseChains new base chains (latest from API).
 * @returns updated base chains.
 */
function removeNewlyRemovedBaseChains(updatedBaseChains: BaseChain[], newBaseChains: BaseChain[]): BaseChain[] {
    const finalBaseChains: BaseChain[] = [];

    // Do not add newly removed base chains (if any) / Add common base chains only.
    for (const updatedBaseChain of updatedBaseChains) {
        if (newBaseChains.find(baseChain => baseChain.name === updatedBaseChain.name)) {
            finalBaseChains.push(updatedBaseChain);
        }
    }

    return finalBaseChains;
}

/**
 * Updates the alerts of all of the chains within each base chain.
 * @param baseChains base chains to be updated.
 * @returns updated base chains.
 */
async function updateBaseChainsWithAlerts(baseChains: BaseChain[]): Promise<BaseChain[]> {
    // Populate each active chain within each base chain.
    for (const updatedBaseChain of baseChains) {
        for (let chain of updatedBaseChain.chains) {
            if (chain.active) {
                chain = await AlertsOverviewAPI.updateAlerts(chain);
            }
        }
    }

    return baseChains;
}

/**
 * Updates active chains within a respective base chain.
 * @param baseChains base chains which contains the respective base chain.
 * @param baseChainName name of base chain to be updated.
 * @param selectedChains list of name of selected chains.
 * @returns updated base chains.
 */
function updateActiveChainsInBaseChain(baseChains: BaseChain[], baseChainName: string, selectedChains: string[]): BaseChain[] {
    const updatedBaseChains: BaseChain[] = [];

    for (const updatedBaseChain of baseChains) {
        if (updatedBaseChain.name === baseChainName) {
            for (const updatedChain of updatedBaseChain.chains) {
                updatedChain.active = selectedChains.length === 0 || selectedChains.includes(updatedChain.name);
            }
        }
        updatedBaseChains.push(updatedBaseChain);
    }

    return updatedBaseChains
}

/**
 * ALERTS OVERVIEW
 * 
 * The functions below are used within the panic-alerts-overview component.
 * The logic within this component consists of having an array of chains. These
 * chains are then updated with the data as required. The logic below also takes
 * into account when chains are removed or added while PANIC UI is running.
 */

/**
 * Gets the chains from the API and formats them with the chain information.
 * @returns list of populated chains.
 */
async function getChains(): Promise<Chain[]> {
    const data: any = await getMonitorablesInfo();
    const chains: Chain[] = [];

    for (const baseChain in data.result) {
        if (data.result[baseChain]) {
            for (const currentChain in data.result[baseChain]) {
                // Skip chain if monitored field does not exist.
                if (!data.result[baseChain][currentChain].monitored) {
                    continue;
                }

                // Get Systems.
                const currentSystems: string[] = getSystems(data.result[baseChain][currentChain].monitored.systems);
                // Get Repos.
                const currentRepos: string[] = getRepos(data.result[baseChain][currentChain].monitored);

                // Skip chain if it does not contain any monitorable sources.
                if (currentSystems.length + currentRepos.length === 0) {
                    continue;
                }

                chains.push({
                    name: currentChain,
                    id: data.result[baseChain][currentChain].parent_id,
                    repos: currentRepos,
                    systems: currentSystems,
                    alerts: [],
                    active: true
                });
            }
        }
    }

    return chains;
}

/**
 * Adds newly added chains and removes newly removed chains.
 * @param chains chains to be updated.
 * @returns updated chains.
 */
async function updateChains(chains: Chain[]): Promise<Chain[]> {
    const finalChains: Chain[] = [];
    const newChains: Chain[] = await getChains();

    // Check for newly added/removed chains.
    for (const newChain of newChains) {
        // Add newly added chains (if any).
        if (!chains.find(chain => chain.id === newChain.id)) {
            newChain.active = false;
            finalChains.push(newChain);
        }
    }

    // Do not add newly removed chains (if any) / Add common chains only.
    for (const chain of chains) {
        if (newChains.find(newChain => newChain.id === chain.id)) {
            finalChains.push(chain);
        }
    }

    return finalChains;
}

/**
 * Returns the sources of active chains.
 * @param chains chains to be checked.
 * @returns list of name of sources of active chains.
 */
function activeChainsSources(chains: Chain[]): string[] {
    const sources: string[] = [];

    // Filter to active chains only.
    const activeChains = chains.filter(function (chain) {
        return chain.active;
    });

    for (const chain of activeChains) {
        sources.push.apply(sources, chain.systems);
        sources.push.apply(sources, chain.repos);
    }

    return sources;
}

/**
 * Updates active chains.
 * @param chains chains to be updated.
 * @param activeChains list of name of active chains.
 * @returns updated chains.
 */
function updateActiveChains(chains: Chain[], activeChains: string[]): Chain[] {
    const updatedChains: Chain[] = [];

    for (const chain of chains) {
        chain.active = activeChains.length === 0 || activeChains.includes(chain.name);
        updatedChains.push(chain);
    }

    return updatedChains
}

/**
 * BOTH
 * 
 * The functions below are used within both the panic-dashboard-overview and the 
 * panic-alerts-overview components.
 */

/**
 * Returns the value for the chain filter. If not all chains are active, it
 * returns the name of the active chains while if all chains are active, it
 * returns an empty list. This is the case since no chain should be selected
 * if all chains are active.
 * @returns list of name of all selected chains.
 */
function getChainFilterValue(chains: Chain[]): string[] {
    // Filter non-active chains.
    const activeChains = chains.filter(function (chain) {
        return chain.active;
    });

    // If all chains are active, set filter to empty.
    if (activeChains.length === chains.length) {
        return [];
    }

    // Else return name of active chains.
    return activeChains.map(chain => chain.name);
}
