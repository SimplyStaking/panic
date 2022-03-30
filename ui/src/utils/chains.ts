import {BaseChain, SubChain, Repo, Source} from "../interfaces/chains";
import {API_URL, BASE_CHAINS, RepoType} from "./constants";
import {AlertsOverviewAPI} from "./alertsOverview";
import {FilterState} from "../interfaces/filterState";
import {FilterStateAPI} from "./filterState";
import {UnknownRepoTypeError} from "./errors";

export const ChainsAPI = {
    // panic-dashboard-overview
    getAllBaseChains: getAllBaseChains,
    updateBaseChainsWithAlerts: updateBaseChainsWithAlerts,
    getRepoIDsOfRepoType: getRepoIDsOfRepoType,
    // panic-alerts-overview
    getSubChains: getSubChains,
    activeChainsSources: activeChainsSources,
    activeChainsSourcesIDs: activeChainsSourcesIDs,
    // panic-systems-overview
    getBaseChainByName: getBaseChainByName,
}

/**
 * DASHBOARD OVERVIEW
 * The functions below are used within the panic-dashboard-overview component.
 * The logic within this component consists of having an array of base chains
 * which contain an array of chains. These chains within the base chains are
 * then updated with data from the API as required. The logic below also takes
 * into account when base chains and/or sub-chains are removed or added while
 * PANIC UI is running.
 */

/**
 * Gets the monitorable information of the base chains from the API.
 * @param baseChainsNames the names of the base chains as an array.
 * @returns the monitorable information of the base chains as a JSON object.
 */
async function getMonitorablesInfo(baseChainsNames: string[]): Promise<any> {
    try {
        const monitorablesInfo: Response = await fetch(`${API_URL}mongo/monitorablesInfo`,
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
        return {result: {}}
    }
}

/**
 * Gets the specified base chains from the API, parses them and formats them
 * with the chain information.
 * @param baseChainsNames the names of the base chains as an array.
 * @returns array of populated base chains.
 */
async function getBaseChains(baseChainsNames: string[]): Promise<BaseChain[]> {
    const data: any = await getMonitorablesInfo(baseChainsNames);
    const baseChains: BaseChain[] = [];

    for (const baseChain in data.result) {
        if (data.result[baseChain] && data.result[baseChain] !== {}) {
            const currentChains: SubChain[] = [];
            for (const currentChain in data.result[baseChain]) {
                // Skip chain if monitored field does not exist.
                if (!data.result[baseChain][currentChain].monitored) {
                    continue;
                }

                const parentID: string = data.result[baseChain][currentChain].parent_id;

                // Get Systems.
                const systems: Source[] = getSystems(data.result[baseChain][currentChain].monitored.systems);
                // Get Nodes.
                const nodes: Source[] = getNodes(data.result[baseChain][currentChain].monitored.nodes);
                // Get Repos.
                const repos: Repo[] = getRepos(data.result[baseChain][currentChain].monitored);
                // Check whether chain is source in itself.
                const isSource: boolean = isChainSource(data.result[baseChain][currentChain].monitored.chains, parentID);

                const noMonitorableSources: boolean = systems.length + nodes.length + repos.length === 0;

                // Skip chain if it does not contain any monitorable sources.
                if (noMonitorableSources && !isSource) {
                    continue;
                }

                currentChains.push({
                    name: currentChain,
                    id: parentID,
                    systems,
                    nodes,
                    repos,
                    isSource,
                    alerts: []
                });
            }

            // Skip base chain if its chains do not contain any monitorable sources.
            if (currentChains.length == 0) {
                continue;
            }

            baseChains.push({
                name: baseChain,
                subChains: currentChains
            });
        }
    }

    return baseChains;
}

/**
 * Gets all of the base chains from the API. Wrapper around
 * {@link getBaseChains} function.
 * @returns array of populated base chains.
 */
async function getAllBaseChains(): Promise<BaseChain[]> {
    return await getBaseChains(BASE_CHAINS);
}

/**
 * Returns an array of system sources given a systems object.
 * @param systems object retrieved from JSON.
 * @returns array of system sources.
 */
function getSystems(systems: any): Source[] {
    const currentSystems: Source[] = [];

    if (systems) {
        for (const system of systems) {
            const id: string = Object.keys(system)[0];
            currentSystems.push({
                id: id,
                name: system[id]
            });
        }
    }

    return currentSystems;
}

/**
 * Returns an array of node sources given a monitored object.
 * @param nodes object retrieved from JSON.
 * @returns array of node sources.
 */
function getNodes(nodes: any): Source[] {
    const currentNodes: Source[] = [];
    if (nodes) {
        for (const node of nodes) {
            const id: string = Object.keys(node)[0];
            const nodeExists: boolean = currentNodes.some(node => node.id === id);
            if (!nodeExists){
                currentNodes.push({
                    id: id,
                    name: node[id]
                });
            }
        }
    }
    return currentNodes;
}

/**
 * Returns an array of repo sources given a monitored object.
 * This function also categorises the repo's type. Throws
 * an error if an unknown repo type is encountered.
 * @param monitored object retrieved from JSON.
 * @returns array of repo sources.
 */
function getRepos(monitored: any): Repo[] {
    const currentRepos: Repo[] = [];

    for (const type of Object.keys(monitored)) {
        let repoType: RepoType;
        if (type.includes('repos')) {
            if (type.toLowerCase().includes(RepoType.GITHUB.toLowerCase())){
                repoType = RepoType.GITHUB
            } else if (type.toLowerCase().includes(RepoType.DOCKERHUB.toLowerCase())){
                repoType = RepoType.DOCKERHUB
            } else {
                throw new UnknownRepoTypeError(type);
            }
            for (const repo of monitored[type]) {
                const id: string = Object.keys(repo)[0];
                currentRepos.push({
                    id: id,
                    name: repo[id],
                    type: repoType
                });
            }
        }
    }
    return currentRepos;
}

/**
 * Checks whether a sub-chain is a source in itself.
 * @param chains object retrieved from JSON.
 * @param chainID ID of sub chain being checked.
 * @returns true if sub-chain is a source, false otherwise.
 */
function isChainSource(chains: any, chainID: string): boolean {
    if (chains) {
        if (chains.some(chain => Object.keys(chain)[0] === chainID)) {
            return true;
        }
    }

    return false;
}

/**
 * Updates the alerts of all the chains within each base chain.
 * @param baseChains base chains to be updated.
 * @param filterStates only chains and alerts which fall under these filters are
 * required.
 * @returns array of updated base chains.
 */
async function updateBaseChainsWithAlerts(baseChains: BaseChain[], filterStates: FilterState[]): Promise<BaseChain[]> {
    const finalBaseChains: BaseChain[] = [];
    const allActiveChains: SubChain[] = [];

    // Get each active (selected) chain within each base chain.
    for (const baseChain of baseChains) {
        const filterState: FilterState = FilterStateAPI.getFilterState(baseChain.name, filterStates);
        const noFilter: boolean = filterState.selectedSubChains.length === 0;

        for (let chain of baseChain.subChains) {
            if (noFilter || filterState.selectedSubChains.includes(chain.name)) {
                allActiveChains.push(chain);
            }
        }
    }

    const updatedChains = await AlertsOverviewAPI.updateAlerts(allActiveChains);

    // Populate each active (selected) chain within each base chain.
    for (const baseChain of baseChains) {
        for (let chain of baseChain.subChains) {
            const updatedChain: SubChain = updatedChains.find(updatedChain => updatedChain.id === chain.id);
            if (updatedChain !== undefined) {
                chain = updatedChain;
            }
        }
        finalBaseChains.push(baseChain);
    }

    return finalBaseChains;
}

/**
 * Returns the IDs of the repos which have the specified repo type.
 * @param repos array of repo sources to be filtered.
 * @param repoType the repo type required for the IDs to be returned.
 * @returns filtered repo IDs as an array of strings.
 */
function getRepoIDsOfRepoType(repos: Repo[], repoType: RepoType): string[] {
    return repos.reduce((filtered: string[], repo: Repo) => {
        if (repo.type === repoType){
            filtered.push(repo.id);
        }
        return filtered;
    }, []);
}

/**
 * ALERTS OVERVIEW
 *
 * The functions below are used within the panic-alerts-overview component.The
 * logic within this component consists of having an array of sub-chains. These
 * chains are then updated with the data as required. The logic below also takes
 * into account when chains are removed or added while PANIC UI is running.
 */

/**
 * Gets the sub-chains from the API and formats them with the chain information.
 * @returns array of populated sub-chains.
 */
async function getSubChains(): Promise<SubChain[]> {
    const subChains: SubChain[] = [];
    const baseChains: BaseChain[] = await getAllBaseChains();

    for (const baseChain of baseChains) {
        subChains.push.apply(subChains, baseChain.subChains);
    }

    return subChains;
}

/**
 * Returns the sources of active (selected) sub-chains.
 * @param subChains array of sub-chains.
 * @param selectedChains array of chain names to be checked (active/selected).
 * @returns sources of active sub-chains as array of sources.
 */
function activeChainsSources(subChains: SubChain[], selectedChains: string[]): Source[] {
    const sources: Source[] = [];
    const repos: Repo[] = [];
    const noFilter: boolean = selectedChains.length === 0;

    // Filter to active (selected) subChains only.
    const activeChains = subChains.filter(function (chain) {
        return noFilter || selectedChains.includes(chain.name);
    });

    for (const chain of activeChains) {
        sources.push.apply(sources, chain.systems);
        sources.push.apply(sources, chain.nodes);
        repos.push.apply(repos, chain.repos);
        if (chain.isSource)
            sources.push({
                id: chain.id,
                name: chain.name
            })
    }

    // If we have common repos, update repo name to show whether GitHub/DockerHub.
    repos.forEach(function(repo) {
        const indexes = repos.reduce((a, r, rIndex) => {
            if(r.name === repo.name)
                a.push(rIndex);
            return a;
        }, [])
        if (indexes.length > 1) {
            for (const index of indexes) {
                repos[index] = {
                    name: `${repos[index].name} (${repos[index].type})`,
                    id: repos[index].id,
                    type: repos[index].type
                };
            }
        }
    }, repos);

    sources.push.apply(sources, repos);

    // Remove any duplicate sources (common id and name).
    return sources.filter((source1, index, self) =>
        index === self.findIndex((source2) => (
            source1.id === source2.id && source1.name === source2.name
        ))
    );
}

/**
 * Returns the IDs of the sources of active (selected) sub-chains.
 * @param subChains array of sub-chains.
 * @param selectedChains array of chain names to be checked (active/selected).
 * @returns sources IDs of active sub-chains as array of strings.
 */
function activeChainsSourcesIDs(subChains: SubChain[], selectedChains: string[]): string[] {
    return activeChainsSources(subChains, selectedChains).map((source) => {return source.id});
}

/**
 * SYSTEMS OVERVIEW
 * The functions below are used within the panic-systems-overview component.
 * The logic within this component consists of having an array of sub-chains.
 * The chains are then updated with metrics.
 */

/**
 * Gets the base chain with the specified base chain name from the API.
 * If the specified base chain is not found, null is returned.
 * @param baseChainName name of the base chain to be returned.
 * @returns base chain if found, otherwise null.
 */
async function getBaseChainByName(baseChainName: string): Promise<BaseChain> {
    const baseChains: BaseChain[] = await getBaseChains([baseChainName]);

    if (baseChains.length !== 1) {
        return null;
    }

    return baseChains[0];
}
